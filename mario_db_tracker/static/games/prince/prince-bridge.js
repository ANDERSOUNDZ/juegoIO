/**
 * PrinceBridge — Conecta HandInput de PIXO Therapy con SDLPoP WASM
 */
class PrinceBridge {
    /**
     * @param {HandInput} handInput - Instancia de HandInput de PIXO
     * @param {Object} Module - Módulo Emscripten (global Module)
     */
    constructor(handInput, Module) {
        this.handInput = handInput;
        this.Module = Module;
        this.fingerMap = {
            '0': 'left',    // Pulgar → izquierda
            '1': 'jump',    // Índice → saltar
            '2': 'right',   // Medio → derecha
            '3': 'down',    // Anular → agacharse
            '4': 'action',  // Meñique → acción (shift)
        };
        this.active = false;
        this._lastState = null;
        this._animFrame = null;
        this._onGameOver = null;
        this._onStateChange = null;
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

    start() {
        if (this.active) return;
        this.active = true;
        if (this.Module._pop_enable_hand_tracking) {
            this.Module._pop_enable_hand_tracking();
        }
        this._tick();
    }

    stop() {
        this.active = false;
        if (this._animFrame) {
            cancelAnimationFrame(this._animFrame);
            this._animFrame = null;
        }
        if (this.Module._pop_disable_hand_tracking) {
            this.Module._pop_disable_hand_tracking();
        }
    }

    _tick() {
        if (!this.active) return;

        // Leer acciones de los dedos via HandInput
        const actions = this.handInput.getMappedActions(this.fingerMap);

        let x = 0, y = 0, shift = 0;

        // Mapeo de acciones a controles del juego
        if (actions.left) x = -1;
        else if (actions.right) x = 1;

        if (actions.jump || actions.up) y = -1;
        else if (actions.down) y = 1;

        if (actions.interact || actions.action) shift = 1;

        // Enviar controles al WASM
        if (this.Module._pop_set_hand_control) {
            this.Module._pop_set_hand_control(x, y, shift);
        }

        // Leer estado del juego para analytics
        try {
            const state = {
                level: this.Module._pop_get_current_level(),
                minutes: this.Module._pop_get_remaining_minutes(),
                ticks: this.Module._pop_get_remaining_ticks(),
                hp: this.Module._pop_get_hitpoints(),
                alive: this.Module._pop_get_kid_alive(),
                gameOver: this.Module._pop_is_game_over() !== 0,
                nextLevel: this.Module._pop_get_next_level(),
            };

            // Detectar cambios de estado
            const prev = this._lastState;
            if (!prev || state.level !== prev.level || state.gameOver !== prev.gameOver) {
                if (this._onStateChange) this._onStateChange(state);
            }

            // Detectar game over
            if (state.gameOver && (!prev || !prev.gameOver)) {
                if (this._onGameOver) this._onGameOver(state);
            }

            this._lastState = state;
        } catch (e) {
            // Module might not be ready yet
        }

        this._animFrame = requestAnimationFrame(() => this._tick());
    }

    getGameState() {
        return this._lastState;
    }
}

// Exportar al window
window.PrinceBridge = PrinceBridge;
