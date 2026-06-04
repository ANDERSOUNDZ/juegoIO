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
        this.nostalgist = null;
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

    async start(romUrl) {
        if (this.active) return;
        this.active = true;

        this.nostalgist = await Nostalgist.launch({
            core: 'fceumm',
            rom: romUrl,
            canvas: this._createCanvas(),
        });

        this._tick();
    }

    stop() {
        this.active = false;
        if (this._animFrame) {
            cancelAnimationFrame(this._animFrame);
            this._animFrame = null;
        }
        if (this.nostalgist) {
            this.nostalgist.exit();
            this.nostalgist = null;
        }
    }

    _createCanvas() {
        this.container.innerHTML = '';
        var canvas = document.createElement('canvas');
        canvas.className = 'emscripten';
        canvas.style.width = '768px';
        canvas.style.height = '720px';
        canvas.style.imageRendering = 'pixelated';
        canvas.style.imageRendering = 'crisp-edges';
        this.container.appendChild(canvas);
        return canvas;
    }

    _tick() {
        if (!this.active || !this.nostalgist) return;

        var actions = this.handInput.getMappedActions(this.fingerMap);

        if (actions.left) this.nostalgist.pressDown('left');
        else this.nostalgist.pressUp('left');

        if (actions.right) this.nostalgist.pressDown('right');
        else this.nostalgist.pressUp('right');

        if (actions.jump || actions.up) this.nostalgist.pressDown('a');
        else this.nostalgist.pressUp('a');

        if (actions.down) this.nostalgist.pressDown('down');
        else this.nostalgist.pressUp('down');

        if (actions.run || actions.action) this.nostalgist.pressDown('b');
        else this.nostalgist.pressUp('b');

        if (actions.start) {
            this.nostalgist.press('start', { time: 50 });
            actions.start = false;
        }

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
