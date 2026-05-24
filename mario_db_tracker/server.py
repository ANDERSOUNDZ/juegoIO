import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os
import time
import threading
import queue
import numpy as np
import json
import base64
import psycopg2
from flask import Flask, render_template, jsonify
from flask_sock import Sock

# ─── CONFIG ──────────────────────────────────────────
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "mario_db"
DB_USER = "postgres"
DB_PASSWORD = "admin"

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = "hand_landmarker.task"
NUM_HANDS = 1
HEARTBEAT_MS = 200

# ─── GLOBALS ─────────────────────────────────────────
nivel_atual = 1
lock_nivel = threading.Lock()

# ─── DB WORKER ASINCRONO ─────────────────────────────
class DBWorker:
    def __init__(self):
        self.q = queue.Queue(maxsize=100)
        self.running = False
        self.thread = None
        self.conn = None
        self.cursor = None

    def _connect(self):
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, database=DB_NAME,
                user=DB_USER, password=DB_PASSWORD
            )
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            print("[DB] Conectado a PostgreSQL")
            return True
        except Exception as e:
            print(f"[DB] Error conexion: {e}")
            return False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[DB] Worker iniciado")

    def stop(self):
        self.running = False
        try:
            self.q.put(None, block=False)
        except queue.Full:
            pass
        if self.thread:
            self.thread.join(timeout=2)
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("[DB] Worker detenido")

    def send(self, nivel, pulgar, indice, medio, anular, menique):
        try:
            if self.q.full():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put_nowait((nivel, pulgar, indice, medio, anular, menique))
        except Exception:
            pass

    def _run(self):
        self._connect()
        while self.running:
            try:
                item = self.q.get(timeout=1)
                if item is None:
                    break
                n, pg, i, m, a, mn = item
                if self.conn and self.cursor:
                    try:
                        self.cursor.execute(
                            "INSERT INTO control_juego (nivel, pulgar, indice, medio, anular, menique) VALUES (%s,%s,%s,%s,%s,%s)",
                            (n, pg, i, m, a, mn),
                        )
                    except Exception as e:
                        print(f"[DB] Error insert: {e}")
                        self._connect()
                self.q.task_done()
            except queue.Empty:
                continue

# ─── DOWNLOAD MODEL AT STARTUP ───────────────────────
def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("[SERVER] Descargando modelo...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[SERVER] Descargado")

# ─── HAND CONNECTIONS FOR DRAWING ────────────────────
CONEXIONES = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
]

# ─── FLASK APP ───────────────────────────────────────
app = Flask(__name__)
sock = Sock(app)

# Shared DB worker (started once)
db = DBWorker()
db.start()

ensure_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_nivel/<int:n>')
def set_nivel(n):
    global nivel_atual
    if 1 <= n <= 5:
        with lock_nivel:
            nivel_atual = n
        print(f"[SERVER] Nivel cambiado a {n}")
    return jsonify({"nivel": nivel_atual})

@sock.route('/ws')
def ws_handler(ws):
    """WebSocket: recibe frames JPEG del cliente, procesa con MediaPipe,
    devuelve JSON con datos de dedos + frame anotado en base64."""
    global nivel_atual

    base_opts = python.BaseOptions(model_asset_path=MODEL_PATH)
    opts = vision.HandLandmarkerOptions(
        base_options=base_opts,
        num_hands=NUM_HANDS,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        running_mode=vision.RunningMode.VIDEO,
    )
    detector = vision.HandLandmarker.create_from_options(opts)

    start_time = time.time()
    ultimo_estado = (0, 0, 0, 0, 0)
    ultimo_envio = 0
    # Sensitivity per finger (0-100, default 50)
    # Controls how much a finger must bend/extend to toggle state.
    # Higher value = triggers easier (less bend needed)
    # Lower value = needs more obvious bend to trigger
    sens = [50, 50, 50, 50, 50]
    # Hysteresis: current confirmed state per finger, avoids jitter
    finger_state = [0, 0, 0, 0, 0]

    print("[WS] Cliente conectado")

    try:
        while True:
            data = ws.receive()
            if data is None:
                break

            # Check for config messages (JSON string)
            if isinstance(data, str):
                try:
                    msg = json.loads(data)
                    if msg.get('type') == 'config':
                        sens = [max(0, min(100, s)) for s in msg.get('sensitivity', sens)]
                        print(f"[WS] Sensibilidad actualizada: {sens}")
                        continue
                except (json.JSONDecodeError, ValueError):
                    pass
                # base64 encoded frame
                jpg_bytes = base64.b64decode(data)
            else:
                jpg_bytes = data

            arr = np.frombuffer(jpg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            ts = int((time.time() - start_time) * 1000)
            frame = cv2.flip(frame, 1)  # mirror horizontal (efecto espejo)
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect_for_video(mp_img, ts)

            pg = i_ = m = a = mn = 0

            if result.hand_landmarks:
                lm = result.hand_landmarks[0]
                mano = result.handedness[0][0].category_name

                # Sensitivity → threshold mapping:
                # sens=0  → threshold=0.12 (needs very clear extension)
                # sens=50 → threshold=0.04 (moderate)
                # sens=100→ threshold=0.00 (any tiny movement)
                #
                # Hysteresis: to turn ON a finger needs to pass threshold,
                # to turn OFF it needs to go below (threshold - margin).
                # This prevents flickering at the boundary.
                HYST_MARGIN = 0.02

                def calc_threshold(s):
                    return (100 - s) / 100.0 * 0.12

                def check_finger_hyst(diff, s, current_state):
                    thresh = calc_threshold(s)
                    if current_state == 0:
                        return 1 if diff > thresh else 0
                    else:
                        return 0 if diff < (thresh - HYST_MARGIN) else 1

                # Fingers: diff = tip.y - pip.y (positive = finger BENT/curled down)
                diffs = [
                    0,  # thumb handled separately
                    lm[8].y  - lm[6].y,   # index
                    lm[12].y - lm[10].y,   # middle
                    lm[16].y - lm[14].y,   # ring
                    lm[20].y - lm[18].y,   # pinky
                ]

                # Thumb: measure distance from thumb tip (4) to index MCP (5).
                # When thumb is OPEN → distance is large.
                # When thumb is CURLED → distance is small.
                # We invert: diff = (open_ref - current_dist) so positive = curled.
                import math
                thumb_dist = math.sqrt((lm[4].x - lm[5].x)**2 + (lm[4].y - lm[5].y)**2)
                # Reference: distance from wrist(0) to middle MCP(9) as hand-size normalizer
                hand_size = math.sqrt((lm[0].x - lm[9].x)**2 + (lm[0].y - lm[9].y)**2)
                if hand_size > 0.01:
                    # Normalized: ~0.6 when open, ~0.15 when curled
                    norm_dist = thumb_dist / hand_size
                    # Invert so positive = curled. 0.4 is approx midpoint.
                    diffs[0] = 0.4 - norm_dist
                else:
                    diffs[0] = 0

                pg = check_finger_hyst(diffs[0], sens[0], finger_state[0])
                i_ = check_finger_hyst(diffs[1], sens[1], finger_state[1])
                m  = check_finger_hyst(diffs[2], sens[2], finger_state[2])
                a  = check_finger_hyst(diffs[3], sens[3], finger_state[3])
                mn = check_finger_hyst(diffs[4], sens[4], finger_state[4])

                finger_state = [pg, i_, m, a, mn]

                # Draw landmarks on frame
                coords = [(int(l.x * w), int(l.y * h)) for l in lm]
                for a_, b_ in CONEXIONES:
                    cv2.line(frame, coords[a_], coords[b_], (255, 0, 0), 2)
                for pt in coords:
                    cv2.circle(frame, pt, 4, (0, 255, 0), -1)
                cv2.putText(frame, mano, (coords[0][0]-30, coords[0][1]+30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            else:
                # No hand detected → all fingers off
                finger_state = [0, 0, 0, 0, 0]
                pg = i_ = m = a = mn = 0

            with lock_nivel:
                nv = nivel_atual

            labels = [("Pulgar", pg), ("Indice", i_), ("Medio", m), ("Anular", a), ("Menique", mn)]
            cv2.rectangle(frame, (10,10), (280,150), (0,0,0), -1)
            cv2.putText(frame, f"NIVEL: {nv}", (20,35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
            for j, (nom, val) in enumerate(labels):
                color = (0,255,0) if val else (0,0,255)
                cv2.putText(frame, f"{nom}: {val}", (20, 60+j*18),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Encode annotated frame
            ret_jpg, jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame_b64 = base64.b64encode(jpg.tobytes()).decode('ascii') if ret_jpg else ""

            # DB logging
            estado = (pg, i_, m, a, mn)
            if estado != ultimo_estado or (ts - ultimo_envio >= HEARTBEAT_MS):
                db.send(nv, pg, i_, m, a, mn)
                ultimo_envio = ts
                if estado != ultimo_estado:
                    print(f"[DB] N{nv} P:{pg} I:{i_} M:{m} A:{a} Mn:{mn}")
                    ultimo_estado = estado

            # Send response
            ws.send(json.dumps({
                "fingers": [pg, i_, m, a, mn],
                "nivel": nv,
                "frame": frame_b64,
            }))

    except Exception as e:
        print(f"[WS] Desconectado: {e}")
    finally:
        detector.close()
        print("[WS] Cliente desconectado")

# ─── INICIO ──────────────────────────────────────────
if __name__ == '__main__':
    print("\n[SERVER] Abre http://localhost:5000 en tu navegador")
    print("[SERVER] La camara se activa en el CLIENTE (navegador)")
    print("[SERVER] Presiona Ctrl+C para detener\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
