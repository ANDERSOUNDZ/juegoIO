const HYST_MARGIN = 0.02;

class HandInput {
    constructor() {
        this.fingers = [0, 0, 0, 0, 0];
        this.landmarks = null;
        this.sensitivity = [50, 50, 50, 50, 50];
        this._onFrame = null;
        this._onFingers = null;
        this._onConnect = null;
        this._video = null;
        this._ws = null;
        this._hands = null;
        this._connected = false;
        this._running = false;
        this._stream = null;
        this._fSt = [0, 0, 0, 0, 0];
        this._sessionId = null;
    }

    setSensitivity(arr) {
        this.sensitivity = arr.map(s => Math.max(0, Math.min(100, s)));
        if (this._connected) {
            this.sendMessage({ type: 'config', sensitivity: this.sensitivity });
        }
    }

    onFrame(callback) {
        this._onFrame = callback;
    }

    onFingers(callback) {
        this._onFingers = callback;
    }

    onConnect(callback) {
        this._onConnect = callback;
    }

    getFingers() {
        return this.fingers;
    }

    getMappedActions(fingerMap) {
        const actions = { jump: false, right: false, left: false };
        for (let i = 0; i < 5; i++) {
            if (this.fingers[i] === 1) {
                const action = fingerMap[String(i)] || fingerMap[i];
                if (action && action !== 'none') {
                    actions[action] = true;
                }
            }
        }
        return actions;
    }

    sendMessage(msg) {
        if (this._ws && this._ws.readyState === WebSocket.OPEN) {
            this._ws.send(JSON.stringify(msg));
        }
    }

    setSendFrame() {}

    getVideoElement() {
        return this._video;
    }

    disconnect() {
        this._running = false;
        if (this._ws) this._ws.close();
        if (this._stream) {
            this._stream.getTracks().forEach(t => t.stop());
        }
        this._connected = false;
    }

    async connect() {
        const btn = document.getElementById('btn-camera');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Iniciando...';
        }

        await this._initCamera();

        if (typeof Hands === 'undefined') {
            throw new Error('MediaPipe no cargado');
        }

        this._hands = new Hands({
            locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${f}`
        });
        this._hands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.7,
            minTrackingConfidence: 0.7,
        });

        this._hands.onResults(results => this._onResults(results));
        await this._hands.initialize();

        this._running = true;
        this._connectWS();

        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Desactivar camara';
            btn.classList.add('active');
        }

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

    _connectWS() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this._ws = new WebSocket(`${proto}//${location.host}/ws`);

        this._ws.onopen = () => {
            this._connected = true;
            this.sendMessage({ type: 'config', sensitivity: this.sensitivity });
            if (this._onConnect) this._onConnect();
        };

        this._ws.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data);
                if (msg.type === 'session_created' && msg.session_id) {
                    this._sessionId = msg.session_id;
                }
            } catch (e) {
                console.error('[HandInput] Parse error:', e);
            }
        };

        this._ws.onclose = () => {
            this._connected = false;
        };

        this._ws.onerror = () => {};
    }

    _onResults(results) {
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            const lm = results.multiHandLandmarks[0];
            this.landmarks = lm.map(l => [l.x, l.y, l.z]);

            const diffs = this._computeDiffs(lm);
            this._fSt = this._detectFingers(diffs);
            this.fingers = [...this._fSt];

            if (this._onFingers) {
                this._onFingers(this.fingers);
            }

            this._sendFingerUpdate();
        } else {
            if (this._fSt.some(v => v !== 0)) {
                this._fSt = [0, 0, 0, 0, 0];
                this.fingers = [0, 0, 0, 0, 0];
                this.landmarks = null;
                if (this._onFingers) this._onFingers(this.fingers);
            }
        }
    }

    _computeDiffs(lm) {
        const diffs = [
            0,
            lm[8].y - lm[6].y,
            lm[12].y - lm[10].y,
            lm[16].y - lm[14].y,
            lm[20].y - lm[18].y,
        ];
        const td = Math.hypot(lm[4].x - lm[5].x, lm[4].y - lm[5].y);
        const hs = Math.hypot(lm[0].x - lm[9].x, lm[0].y - lm[9].y);
        diffs[0] = hs > 0.01 ? 0.4 - td / hs : 0;
        return diffs;
    }

    _detectFingers(diffs) {
        return diffs.map((d, i) => {
            const s = this.sensitivity[i];
            const t = (100 - s) / 100 * 0.12;
            if (this._fSt[i] === 0) {
                return d > t ? 1 : 0;
            } else {
                return d < t - HYST_MARGIN ? 0 : 1;
            }
        });
    }

    _sendFingerUpdate() {
        if (this._connected && this._sessionId) {
            this._ws.send(JSON.stringify({
                type: 'finger_update',
                session_id: this._sessionId,
                fingers: this.fingers,
                landmarks: this.landmarks,
            }));
        }
    }

    _loop() {
        if (!this._running) return;
        if (this._hands && this._video && this._video.readyState >= 2) {
            this._hands.send({ image: this._video }).catch(() => {});
        }
        requestAnimationFrame(() => this._loop());
    }
}
