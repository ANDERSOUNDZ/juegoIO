class SMB3Bridge {
    constructor(handInput, container) {
        this.handInput = handInput;
        this.container = container;
        this.fingerMap = {
            '0': 'left',
            '1': 'jump',
            '2': 'right',
            '3': 'run',
            '4': 'start',
        };
        this.active = false;
        this._animFrame = null;
        this._onGameOver = null;
        this._onStateChange = null;
        this.nes = null;
        this.canvas = null;
        this.ctx = null;
        this.screenBuffer = new ArrayBuffer(256 * 240 * 4);
        this.screenBuf8 = new Uint8ClampedArray(this.screenBuffer);
        this.screenBuf32 = new Uint32Array(this.screenBuffer);
        this.audioCtx = null;
        this.audioEnabled = false;
        this.frameCount = 0;
    }

    setFingerMap(map) {
        this.fingerMap = Object.assign({}, map);
    }

    onGameOver(callback) {
        this._onGameOver = callback;
    }

    onStateChange(callback) {
        this._onStateChange = callback;
    }

    async loadROM(url) {
        const self = this;
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.overrideMimeType('text/plain; charset=x-user-defined');
            xhr.onload = function () {
                if (this.status === 200) {
                    resolve(this.responseText);
                } else {
                    reject(new Error('Failed to load ROM'));
                }
            };
            xhr.onerror = () => reject(new Error('Network error'));
            xhr.send();
        }).then((data) => {
            this.nes = new jsnes.NES({
                onFrame: (fb) => this._onFrame(fb),
                onAudioSample: (l, r) => this._onAudioSample(l, r),
            });
            this.nes.loadROM(data);
        });
    }

    start() {
        if (this.active) return;
        this.active = true;
        this._setupCanvas();
        this._setupAudio();
        this._lastState = null;
        this._tick();
    }

    stop() {
        this.active = false;
        if (this._animFrame) {
            cancelAnimationFrame(this._animFrame);
            this._animFrame = null;
        }
        if (this.audioCtx) {
            this.audioCtx.close();
            this.audioCtx = null;
        }
    }

    _setupCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = 256;
        this.canvas.height = 240;
        this.canvas.style.imageRendering = 'pixelated';
        this.canvas.style.imageRendering = 'crisp-edges';
        this.canvas.style.width = '768px';
        this.canvas.style.height = '720px';
        this.canvas.className = 'emscripten';
        this.container.innerHTML = '';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this.imageData = this.ctx.createImageData(256, 240);
        for (let i = 0; i < this.screenBuf32.length; i++) {
            this.screenBuf32[i] = 0xff000000;
        }
    }

    _setupAudio() {
        try {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            this.audioEnabled = true;
        } catch (e) {
            this.audioEnabled = false;
        }
    }

    _onFrame(framebuffer) {
        for (let y = 0; y < 240; y++) {
            for (let x = 0; x < 256; x++) {
                const i = y * 256 + x;
                const p = framebuffer[i];
                this.screenBuf32[i] = 0xff000000 | p;
            }
        }
        this.imageData.data.set(this.screenBuf8);
        if (this.ctx) {
            this.ctx.putImageData(this.imageData, 0, 0);
        }
    }

    _onAudioSample(left, right) {
        if (!this.audioEnabled || !this.audioCtx) return;
        try {
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }
        } catch (e) { }
    }

    _tick() {
        if (!this.active || !this.nes) return;

        const actions = this.handInput.getMappedActions(this.fingerMap);

        const BUTTON = {
            A: 0,
            B: 1,
            SELECT: 2,
            START: 3,
            UP: 4,
            DOWN: 5,
            LEFT: 6,
            RIGHT: 7,
        };

        this.nes.buttonDown(1, BUTTON.LEFT);
        this.nes.buttonDown(1, BUTTON.RIGHT);
        this.nes.buttonDown(1, BUTTON.UP);
        this.nes.buttonDown(1, BUTTON.DOWN);

        if (actions.left) this.nes.buttonDown(1, BUTTON.LEFT);
        else this.nes.buttonUp(1, BUTTON.LEFT);

        if (actions.right) this.nes.buttonDown(1, BUTTON.RIGHT);
        else this.nes.buttonUp(1, BUTTON.RIGHT);

        if (actions.jump || actions.up) this.nes.buttonDown(1, BUTTON.A);
        else this.nes.buttonUp(1, BUTTON.A);

        if (actions.down) this.nes.buttonDown(1, BUTTON.DOWN);
        else this.nes.buttonUp(1, BUTTON.DOWN);

        if (actions.run || actions.action) this.nes.buttonDown(1, BUTTON.B);
        else this.nes.buttonUp(1, BUTTON.B);

        if (actions.start) this.nes.buttonDown(1, BUTTON.START);
        else this.nes.buttonUp(1, BUTTON.START);

        this.nes.frame();
        this.frameCount++;

        if (this._onStateChange && this.frameCount % 60 === 0) {
            try {
                this._onStateChange({ frameCount: this.frameCount });
            } catch (e) { }
        }

        this._animFrame = requestAnimationFrame(() => this._tick());
    }
}

window.SMB3Bridge = SMB3Bridge;
