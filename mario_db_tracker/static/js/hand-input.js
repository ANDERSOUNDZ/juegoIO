/**
 * HandInput — Reusable WebSocket client for hand tracking.
 * Captures webcam, sends frames to server, receives finger states + annotated frame.
 */
class HandInput {
    constructor() {
        this.ws = null;
        this.fingers = [0, 0, 0, 0, 0];
        this.landmarks = null;
        this.sensitivity = [50, 50, 50, 50, 50];
        this._onFrame = null;
        this._onFingers = null;
        this._onConnect = null;
        this._video = null;
        this._canvas = null;
        this._ctx = null;
        this._connected = false;
        this._sending = false;
        this._sendFrame = false; // Whether server should send annotated frame back
    }

    setSensitivity(arr) {
        this.sensitivity = arr.map(s => Math.max(0, Math.min(100, s)));
        if (this._connected) {
            this.sendMessage({ type: 'config', sensitivity: this.sensitivity });
        }
    }

    onFrame(callback) {
        this._onFrame = callback;
        this._sendFrame = true; // Client wants annotated frames
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
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(msg));
        }
    }

    /**
     * Connect camera + WebSocket. Returns Promise that resolves when camera is ready.
     */
    connect() {
        const cameraPromise = this._initCamera();
        this._connectWS();
        return cameraPromise;
    }

    /** Enable/disable server sending annotated frames back */
    setSendFrame(enabled) {
        this._sendFrame = enabled;
        if (this._connected) {
            this.sendMessage({ type: 'set_send_frame', enabled });
        }
    }

    /** Get the local video element (for showing raw camera feed) */
    getVideoElement() {
        return this._video;
    }

    disconnect() {
        this._sending = false;
        if (this.ws) this.ws.close();
        if (this._video && this._video.srcObject) {
            this._video.srcObject.getTracks().forEach(t => t.stop());
        }
    }

    /**
     * Initialize camera. Returns a Promise that resolves when camera is ready
     * or rejects on error.
     */
    _initCamera() {
        this._video = document.getElementById('camera') || document.createElement('video');
        this._canvas = document.getElementById('send-canvas') || document.createElement('canvas');
        this._canvas.width = 640;
        this._canvas.height = 480;
        this._ctx = this._canvas.getContext('2d');

        this._cameraReady = navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' }
        }).then(stream => {
            this._video.srcObject = stream;
            this._video.play();
            console.log('[HandInput] Camera ready');
        });

        return this._cameraReady;
    }

    _connectWS() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${proto}//${location.host}/ws`);

        this.ws.onopen = () => {
            this._connected = true;
            console.log('[HandInput] Connected');
            // Send initial config
            this.sendMessage({ type: 'config', sensitivity: this.sensitivity });
            this.sendMessage({ type: 'set_send_frame', enabled: this._sendFrame });
            if (this._onConnect) this._onConnect();
            this._startSending();
        };

        this.ws.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data);
                this.fingers = msg.fingers || [0, 0, 0, 0, 0];
                this.landmarks = msg.lm || null;

                // Unlock next frame send (1-in-flight throttle)
                this._waitingResponse = false;

                if (this._onFrame && msg.frame) {
                    this._onFrame(msg.frame, this.fingers, this.landmarks);
                }
                if (this._onFingers) {
                    this._onFingers(this.fingers);
                }
            } catch (e) {
                console.error('[HandInput] Parse error:', e);
            }
        };

        this.ws.onclose = () => {
            this._connected = false;
            this._sending = false;
            console.log('[HandInput] Disconnected, reconnecting in 2s...');
            setTimeout(() => this._connectWS(), 2000);
        };

        this.ws.onerror = (err) => {
            console.error('[HandInput] WS error:', err);
        };
    }

    _startSending() {
        if (this._sending) return;
        this._sending = true;
        this._waitingResponse = false;

        const send = () => {
            if (!this._sending || !this._connected) return;

            // Throttle: only 1 frame in flight at a time (like legacy)
            if (this._waitingResponse) {
                requestAnimationFrame(send);
                return;
            }

            if (this._video && this._video.readyState >= 2) {
                this._ctx.drawImage(this._video, 0, 0, 640, 480);
                this._canvas.toBlob(blob => {
                    if (blob && this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this._waitingResponse = true;
                        blob.arrayBuffer().then(buf => this.ws.send(buf));
                    }
                }, 'image/jpeg', 0.7);
            }

            requestAnimationFrame(send);
        };
        send();
    }
}
