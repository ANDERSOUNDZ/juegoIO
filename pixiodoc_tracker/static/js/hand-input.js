const HYST_MARGIN = 0.05; // histéresis en espacio de fracción de cierre φ (0..1)
const EVENT_FLUSH_INTERVAL = 2000; // ms
const MAX_HANDS = 4; // tope de manos soportadas por el modelo en esta plataforma

// Calibración por dedo de la métrica cruda de flexión: ext = estirado, close = puño.
// La métrica está normalizada al tamaño de la mano (dist muñeca↔nudillo medio),
// así que es independiente de la distancia a la cámara. φ = (d - ext)/(close - ext).
// Ajustable si algún dedo dispara antes/después de lo que muestra el dibujo.
const FLEX_CAL = [
    { ext: -0.10, close: 0.25 }, // pulgar (métrica de distancia, ya relativa a la mano)
    { ext: -0.55, close: 0.20 }, // índice
    { ext: -0.55, close: 0.20 }, // medio
    { ext: -0.50, close: 0.18 }, // anular
    { ext: -0.40, close: 0.15 }, // meñique
];

// MediaPipe Tasks Vision (API actualizada) — se carga dinamicamente como modulo ESM
const TASKS_VISION_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision_bundle.mjs';
const TASKS_VISION_WASM = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm';
const HAND_MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';

class HandInput {
    constructor() {
        // ── Soporte multi-mano ──
        // `this.hands[h]` mantiene el estado independiente de cada mano detectada.
        // Las manos se ordenan de izquierda a derecha (por la x de la muñeca) para
        // que el slot 0 sea siempre estable. Cada juego decide cuántas manos usa
        // via setNumHands(); por defecto 1 (comportamiento legacy idéntico).
        this.numHands = 1;
        this.calibration = FLEX_CAL.map(c => ({ ...c }));  // compartida entre manos
        this.hands = [this._makeHand()];
        this.sensitivities = [[50, 50, 50, 50, 50]];        // una fila por mano

        this._onFrame = null;
        this._onHands = null;       // callback multi-mano: recibe el arreglo de manos
        this._onConnect = null;
        this._video = null;
        this._handLandmarker = null;
        this._lastVideoTime = -1;
        this._connected = false;
        this._running = false;
        this._stream = null;
        this._sessionId = null;
        this._prevState = [0, 0, 0, 0, 0];  // estado previo para registro de eventos (mano 0)
        this._eventBuffer = [];
        this._flushTimer = null;
    }

    /** Estado fresco de una mano. */
    _makeHand() {
        return {
            fingers: [0, 0, 0, 0, 0],
            landmarks: null,
            diffs: [0, 0, 0, 0, 0],
            present: false,
            _fSt: [0, 0, 0, 0, 0],  // estado con histéresis por dedo
        };
    }

    /**
     * Define cuántas manos rastrear (1..MAX_HANDS). Redimensiona los buffers por
     * mano y reconfigura el modelo si ya estaba cargado. Idempotente.
     */
    setNumHands(n) {
        n = Math.max(1, Math.min(MAX_HANDS, parseInt(n, 10) || 1));
        this.numHands = n;
        while (this.hands.length < n) this.hands.push(this._makeHand());
        this.hands.length = n;
        while (this.sensitivities.length < n) this.sensitivities.push([50, 50, 50, 50, 50]);
        this.sensitivities.length = n;
        // Reconfigurar el modelo en caliente si ya existe
        if (this._handLandmarker && this._handLandmarker.setOptions) {
            try { this._handLandmarker.setOptions({ numHands: n }); } catch (e) {}
        }
    }

    /** Sensibilidad de una mano concreta. */
    setSensitivityForHand(h, arr) {
        if (!arr) return;
        if (!this.sensitivities[h]) this.sensitivities[h] = [50, 50, 50, 50, 50];
        this.sensitivities[h] = arr.map(s => Math.max(0, Math.min(100, s)));
    }

    /** Sensibilidad de todas las manos a la vez (arreglo de arreglos). */
    setSensitivities(arrs) {
        if (!Array.isArray(arrs)) return;
        arrs.forEach((a, h) => this.setSensitivityForHand(h, a));
    }

    /**
     * Umbral de cierre (fracción φ ∈ [0,1]) que debe superar el dedo i de la mano h
     * para contar como flexionado. Misma unidad que usa el dibujo de referencia:
     *   sensibilidad alta → φ≈0 (basta empezar a cerrar)
     *   sensibilidad baja → φ≈1 (hay que cerrar el puño)
     */
    flexionTarget(i, h = 0) {
        const sens = this.sensitivities[h] || this.sensitivities[0];
        return (100 - sens[i]) / 100;
    }

    /** Fracción de cierre real 0..1 del dedo i a partir de su métrica cruda. */
    _flexFraction(i, d) {
        const c = this.calibration[i];
        const span = c.close - c.ext;
        if (Math.abs(span) < 1e-4) return 0;
        return Math.max(0, Math.min(1, (d - c.ext) / span));
    }

    /** Métrica cruda de flexión del último frame de la mano h (para calibrar). */
    getRawDiffs(h = 0) {
        const hand = this.hands[h] || this.hands[0];
        return hand.diffs.slice();
    }

    /** Fracción de cierre actual (0..1) del dedo i de la mano h, en vivo. */
    flexFractionLive(i, h = 0) {
        const hand = this.hands[h] || this.hands[0];
        return this._flexFraction(i, hand.diffs[i]);
    }

    /** Aplica calibración por dedo. Ignora entradas nulas (deja el valor previo). */
    applyCalibration(arr) {
        for (let i = 0; i < 5; i++) {
            if (arr[i]) this.calibration[i] = { ext: arr[i].ext, close: arr[i].close };
        }
    }

    onFrame(callback) {
        this._onFrame = callback;
    }

    /** Callback multi-mano: se invoca con el arreglo `this.hands` cada frame. */
    onHands(callback) {
        this._onHands = callback;
    }

    onConnect(callback) {
        this._onConnect = callback;
    }

    /** Dedos de la mano h (mano 0 por defecto = legacy). */
    getFingers(h = 0) {
        const hand = this.hands[h] || this.hands[0];
        return hand.fingers;
    }

    /** ¿Hay algún dedo cerrado en cualquiera de las manos presentes? */
    anyFingerClosed() {
        return this.hands.some(h => h.present && h.fingers.some(f => f === 1));
    }

    /** ¿La mano h está presente en el frame actual? */
    isHandPresent(h = 0) {
        return !!(this.hands[h] && this.hands[h].present);
    }

    /**
     * Resuelve las acciones del juego a partir de los dedos cerrados.
     *  - Si recibe un arreglo de fingerMaps → multi-mano: aplica fingerMaps[h] a la
     *    mano h y combina (OR) los resultados de todas las manos.
     *  - Si recibe un solo objeto fingerMap → lo aplica a la mano 0.
     */
    getMappedActions(fingerMaps) {
        const actions = { jump: false, right: false, left: false, up: false, down: false, interact: false };
        const apply = (fingers, map) => {
            if (!map) return;
            for (let i = 0; i < 5; i++) {
                if (fingers[i] === 1) {
                    const action = map[String(i)] || map[i];
                    if (action && action !== 'none') actions[action] = true;
                }
            }
        };
        if (Array.isArray(fingerMaps)) {
            for (let h = 0; h < this.hands.length; h++) {
                apply(this.hands[h].fingers, fingerMaps[h] || fingerMaps[0]);
            }
        } else {
            apply(this.hands[0].fingers, fingerMaps);  // objeto único → mano 0
        }
        return actions;
    }

    getVideoElement() {
        return this._video;
    }

    disconnect() {
        this._running = false;
        this._flushEvents();
        if (this._flushTimer) {
            clearInterval(this._flushTimer);
            this._flushTimer = null;
        }
        if (this._stream) {
            this._stream.getTracks().forEach(t => t.stop());
        }
        // No cerramos this._handLandmarker: se reutiliza en la siguiente conexion
        // para evitar re-instanciar el WASM (ver nota en preload()).
        this._connected = false;
    }

    /**
     * Carga el bundle WASM de tasks-vision y crea el HandLandmarker (sin camara).
     * Idempotente: si ya esta cargado, no hace nada.
     *
     * IMPORTANTE: tasks-vision es un modulo Emscripten que lee el `window.Module`
     * global al instanciar su WASM. En paginas que tambien corren otro modulo
     * Emscripten (p.ej. los juegos de emulador via Nostalgist, que define window.Module),
     * hay que invocar preload() ANTES de que ese otro modulo defina window.Module,
     * y mantener el landmarker vivo para no re-instanciarlo. Por eso esta separado
     * de connect() y disconnect() no lo destruye.
     */
    async preload() {
        if (this._handLandmarker) return;

        // import() dinamico porque este archivo se sirve como script clasico
        const { FilesetResolver, HandLandmarker } = await import(TASKS_VISION_URL);
        const vision = await FilesetResolver.forVisionTasks(TASKS_VISION_WASM);

        this._handLandmarker = await HandLandmarker.createFromOptions(vision, {
            baseOptions: {
                modelAssetPath: HAND_MODEL_URL,
                delegate: 'GPU',
            },
            numHands: this.numHands,
            runningMode: 'video',
            minHandDetectionConfidence: 0.7,
            minHandPresenceConfidence: 0.7,
            minTrackingConfidence: 0.7,
        });
    }

    async connect() {
        const btn = document.getElementById('btn-camera');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Iniciando...';
        }

        await this._initCamera();
        await this.preload();

        this._lastVideoTime = -1;
        this._running = true;
        this._connected = true;

        this._flushTimer = setInterval(() => this._flushEvents(), EVENT_FLUSH_INTERVAL);

        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Desactivar camara';
            btn.classList.add('active');
        }

        if (this._onConnect) this._onConnect();

        this._loop();
    }

    async _initCamera() {
        this._video = document.getElementById('camera');
        if (!this._video) throw new Error('No hay elemento video#camera');

        this._stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' }
        });
        this._video.srcObject = this._stream;
        await this._video.play();
    }

    _onResults(results) {
        const lms = (results && results.landmarks) || [];

        // Orden estable de manos: de izquierda a derecha por la x de la muñeca.
        // Así el slot 0 corresponde siempre a la mano más a la izquierda en pantalla.
        const order = lms
            .map((lm, idx) => ({ idx, x: lm[0].x }))
            .sort((a, b) => a.x - b.x);

        for (let h = 0; h < this.hands.length; h++) {
            const hand = this.hands[h];
            const src = order[h];
            if (src) {
                const lm = lms[src.idx];
                hand.landmarks = lm.map(l => [l.x, l.y, l.z]);
                hand.present = true;
                hand.diffs = this._computeDiffs(lm);
                hand._fSt = this._detectFingers(hand.diffs, hand._fSt, this.sensitivities[h]);
                hand.fingers = [...hand._fSt];
            } else if (hand.present || hand._fSt.some(v => v !== 0)) {
                hand.present = false;
                hand._fSt = [0, 0, 0, 0, 0];
                hand.fingers = [0, 0, 0, 0, 0];
                hand.landmarks = null;
            }
        }

        if (this._onHands) this._onHands(this.hands);

        this._recordStateChanges();  // registro de eventos: solo mano primaria
    }

    _computeDiffs(lm) {
        // Tamaño de la mano (palma): hace la métrica independiente de la distancia.
        const hs = Math.hypot(lm[0].x - lm[9].x, lm[0].y - lm[9].y) || 0.0001;
        const pip = [null, 6, 10, 14, 18];
        const tip = [null, 8, 12, 16, 20];

        const diffs = [0, 0, 0, 0, 0];
        for (let i = 1; i < 5; i++) {
            // Punta por debajo del nudillo (relativo al tamaño de la mano).
            diffs[i] = (lm[tip[i]].y - lm[pip[i]].y) / hs;
        }
        // Pulgar: cercanía punta↔base índice, relativa al tamaño de la mano.
        const td = Math.hypot(lm[4].x - lm[5].x, lm[4].y - lm[5].y);
        diffs[0] = 0.4 - td / hs;
        return diffs;
    }

    _detectFingers(diffs, fSt, sens) {
        const s = sens || this.sensitivities[0];
        return diffs.map((d, i) => {
            const phi = this._flexFraction(i, d); // 0=estirado, 1=puño
            const target = (100 - s[i]) / 100;
            if (fSt[i] === 0) {
                // >= para que sensibilidad 0 (target=1, puño completo) sí cuente.
                return phi >= target ? 1 : 0;
            } else {
                return phi < target - HYST_MARGIN ? 0 : 1;
            }
        });
    }

    /** Only buffer events when a finger's state actually changes (mano primaria) */
    _recordStateChanges() {
        if (!this._sessionId) return;
        const tipIndices = [4, 8, 12, 16, 20];
        const now = Date.now();
        const fingers = this.hands[0].fingers;
        const lm = this.hands[0].landmarks;
        for (let i = 0; i < 5; i++) {
            if (fingers[i] !== this._prevState[i]) {
                const tip = tipIndices[i];
                this._eventBuffer.push({
                    finger_index: i,
                    state: fingers[i],
                    landmark_x: lm ? lm[tip][0] : null,
                    landmark_y: lm ? lm[tip][1] : null,
                    landmark_z: lm ? lm[tip][2] : null,
                    ts: now,
                });
            }
        }
        this._prevState = [...fingers];
    }

    /** Flush buffered events to the server via HTTP POST */
    _flushEvents() {
        if (!this._sessionId || this._eventBuffer.length === 0) return;
        const events = this._eventBuffer;
        this._eventBuffer = [];
        fetch(`/api/sessions/${this._sessionId}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ events }),
        }).catch(err => {
            console.error('[HandInput] Error flushing events:', err);
        });
    }

    _loop() {
        if (!this._running) return;
        const video = this._video;
        if (this._handLandmarker && video && video.readyState >= 2) {
            // Solo procesar cuando hay un frame nuevo (evita reprocesar el mismo)
            if (video.currentTime !== this._lastVideoTime) {
                this._lastVideoTime = video.currentTime;
                try {
                    const results = this._handLandmarker.detectForVideo(video, performance.now());
                    this._onResults(results);
                } catch (e) {
                    // detectForVideo puede lanzar si el frame aun no esta listo
                }
            }
        }
        requestAnimationFrame(() => this._loop());
    }
}
