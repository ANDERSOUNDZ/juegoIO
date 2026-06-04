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
        canvas.style.width = '100%';
        canvas.style.maxWidth = '768px';
        canvas.style.aspectRatio = '256 / 240';
        canvas.style.imageRendering = 'pixelated';
        canvas.style.imageRendering = 'crisp-edges';
        this.container.appendChild(canvas);
        var self = this;
        setTimeout(function() { self._resizeCanvas(); }, 100);
        window.addEventListener('resize', function() { self._resizeCanvas(); });
        return canvas;
    }

    _resizeCanvas() {
        var canvas = this.container.querySelector('canvas');
        if (!canvas) return;
        var parent = this.container.parentElement;
        if (!parent) return;
        var pw = parent.clientWidth;
        var ph = parent.clientHeight;
        var ratio = 256 / 240;
        if (pw / ph > ratio) {
            canvas.style.width = (ph * ratio) + 'px';
            canvas.style.height = ph + 'px';
        } else {
            canvas.style.width = pw + 'px';
            canvas.style.height = (pw / ratio) + 'px';
        }
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
