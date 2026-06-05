/**
 * emulator-loader.js — Cargador genérico y reutilizable de juegos de emulador.
 *
 * Corre cualquier ROM soportada por libretro (NES, SNES, GB, GBA, Genesis, …)
 * usando Nostalgist.js (https://nostalgist.js.org). Todo es configurable desde
 * la base de datos a través del config del juego — para agregar un juego nuevo
 * NO se toca código: basta una fila en `games` con:
 *
 *   "metadata": { "type": "emulator", ... },
 *   "emulator": {
 *     "core": "fceumm",            // core libretro (ver tabla en create-game.md)
 *     "rom": "emulator/roms/x.nes",// ruta bajo /static/games/ o URL http(s)
 *     "aspectRatio": "256/240",    // "w/h" | [w,h] | número (default 4/3)
 *     "tapButtons": ["start","select"], // botones de pulsación (no sostenidos)
 *     "options": { }               // opciones extra pasadas a Nostalgist.launch
 *   },
 *   "controls": { "fingerMap": { "0": "left", "1": "a", ... } }
 *
 * El fingerMap mapea cada dedo (0..4) directamente a un botón del RetroPad.
 * Nostalgist ya provee fallback de teclado automáticamente.
 */
(function () {
    // Botones estándar del RetroPad de libretro (nombres que entiende Nostalgist)
    var RETROPAD_BUTTONS = [
        'up', 'down', 'left', 'right',
        'a', 'b', 'x', 'y',
        'l', 'r', 'l2', 'r2',
        'select', 'start',
    ];

    function EmulatorGame(opts) {
        opts = opts || {};
        this.handInput = opts.handInput;
        this.container = opts.container;
        this.config = opts.config || {};

        var emu = this.config.emulator || {};
        this.core = emu.core || 'fceumm';
        this.romUrl = EmulatorGame.resolveRom(emu.rom);
        this.aspect = EmulatorGame.parseAspect(emu.aspectRatio);
        this.launchOptions = emu.options || {};
        this.tapButtons = {};
        (emu.tapButtons || ['start', 'select']).forEach(function (b) { this.tapButtons[b] = true; }, this);

        // Multi-mano: un fingerMap por mano. Un emulador tiene muchos botones
        // (NES = 8) y una mano solo 5 dedos, así que puede repartirse en 2 manos.
        var controls = this.config.controls || {};
        this.fingerMaps = Array.isArray(controls.fingerMaps)
            ? controls.fingerMaps.map(function (m) { return Object.assign({}, m); })
            : [Object.assign({}, controls.fingerMap || {})];

        this.nostalgist = null;
        this.active = false;
        this._raf = null;
        this._prev = {};            // estado previo por botón (para tap en flanco)
        this._onStateChange = null;
        this.frameCount = 0;
        var self = this;
        this._resizeHandler = function () { self._resizeCanvas(); };
    }

    // Resuelve la ruta de la ROM: URL absoluta tal cual; ruta relativa contra
    // /static/games/ (donde el blueprint games_static expone games/).
    EmulatorGame.resolveRom = function (rom) {
        if (!rom) return null;
        if (/^(https?:|blob:|data:)/i.test(rom)) return rom;
        var clean = String(rom).replace(/^\/+/, '');
        if (clean.indexOf('static/') === 0) return window.location.origin + '/' + clean;
        return window.location.origin + '/static/games/' + clean;
    };

    // Acepta "256/240", [256,240] o un número; default 4/3.
    EmulatorGame.parseAspect = function (a) {
        if (Array.isArray(a) && a.length === 2 && a[1]) return a[0] / a[1];
        if (typeof a === 'number' && a > 0) return a;
        if (typeof a === 'string' && a.indexOf('/') >= 0) {
            var parts = a.split('/');
            var w = parseFloat(parts[0]), h = parseFloat(parts[1]);
            if (w > 0 && h > 0) return w / h;
        }
        return 4 / 3;
    };

    // Acepta un objeto (1 mano) o un arreglo de objetos (varias manos).
    EmulatorGame.prototype.setFingerMap = function (map) {
        this.fingerMaps = Array.isArray(map)
            ? map.map(function (m) { return Object.assign({}, m); })
            : [Object.assign({}, map)];
    };
    EmulatorGame.prototype.setFingerMaps = EmulatorGame.prototype.setFingerMap;

    EmulatorGame.prototype.onStateChange = function (cb) { this._onStateChange = cb; };

    EmulatorGame.prototype.start = function () {
        if (this.active) return Promise.resolve();
        if (!this.romUrl) return Promise.reject(new Error('EmulatorGame: falta config.emulator.rom'));
        if (typeof Nostalgist === 'undefined') return Promise.reject(new Error('Nostalgist no está cargado'));
        this.active = true;
        var self = this;
        // OJO: la opción de Nostalgist es "element" (no "canvas"). Si se le pasa
        // mal, crea su propio canvas position:fixed a pantalla completa que tapa
        // todo el layout. Le damos NUESTRO canvas (dentro del .emu-frame).
        var launchOpts = Object.assign({
            core: this.core,
            rom: this.romUrl,
            element: this._createCanvas(),
        }, this.launchOptions);
        return Nostalgist.launch(launchOpts).then(function (n) {
            self.nostalgist = n;
            self._tick();
            return n;
        });
    };

    EmulatorGame.prototype.stop = function () {
        this.active = false;
        if (this._raf) { cancelAnimationFrame(this._raf); this._raf = null; }
        window.removeEventListener('resize', this._resizeHandler);
        if (this.nostalgist) {
            try { this.nostalgist.exit(); } catch (e) { /* noop */ }
            this.nostalgist = null;
        }
    };

    EmulatorGame.prototype.restart = function () {
        if (this.nostalgist) { try { this.nostalgist.restart(); } catch (e) { /* noop */ } }
    };

    EmulatorGame.prototype._createCanvas = function () {
        this.container.innerHTML = '';
        // Nostalgist/RetroArch gestiona el width/height del canvas, así que el
        // tamaño lo controla un "frame" contenedor con la proporción del juego
        // (CSS .emu-frame); el canvas solo lo rellena al 100%.
        var frame = document.createElement('div');
        frame.className = 'emu-frame';
        frame.style.aspectRatio = String(this.aspect);
        var canvas = document.createElement('canvas');
        canvas.className = 'emscripten';
        canvas.style.imageRendering = 'pixelated';
        frame.appendChild(canvas);
        this.container.appendChild(frame);
        return canvas;
    };

    // El dimensionado lo hace el CSS (.emu-frame con aspect-ratio); no hace falta
    // recalcular en JS. Se mantiene como no-op por compatibilidad (onResize).
    EmulatorGame.prototype._resizeCanvas = function () { };

    EmulatorGame.prototype._tick = function () {
        if (!this.active || !this.nostalgist) return;

        // getMappedActions con un arreglo de fingerMaps aplica cada mano y hace
        // OR de los botones → varias manos pueden cubrir los 8 botones del NES.
        var actions = this.handInput.getMappedActions(this.fingerMaps);

        for (var i = 0; i < RETROPAD_BUTTONS.length; i++) {
            var btn = RETROPAD_BUTTONS[i];
            var on = !!actions[btn];
            if (this.tapButtons[btn]) {
                // Pulsación única en el flanco de subida (evita repetir start/select)
                if (on && !this._prev[btn]) this.nostalgist.press(btn, { time: 60 });
            } else {
                if (on) this.nostalgist.pressDown(btn);
                else this.nostalgist.pressUp(btn);
            }
            this._prev[btn] = on;
        }

        this.frameCount++;
        if (this._onStateChange && this.frameCount % 60 === 0) {
            try { this._onStateChange({ frameCount: this.frameCount }); } catch (e) { /* noop */ }
        }

        var self = this;
        this._raf = requestAnimationFrame(function () { self._tick(); });
    };

    EmulatorGame.BUTTONS = RETROPAD_BUTTONS;
    window.EmulatorGame = EmulatorGame;
})();
