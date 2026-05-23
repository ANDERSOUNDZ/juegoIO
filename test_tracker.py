import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os
import time
import threading
import queue
import psycopg2

# ─── CONFIGURACION (EDITA AQUI) ─────────────────────
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "mario_db"
DB_USER = "postgres"
DB_PASSWORD = "admin"   # <-- pon tu contraseña real de PostgreSQL

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = "hand_landmarker.task"
NUM_HANDS = 1
NIVEL = 1
HEARTBEAT_MS = 200

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
        data = (nivel, pulgar, indice, medio, anular, menique)
        try:
            if self.q.full():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put_nowait(data)
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

# ─── DESCARGA MODELO ─────────────────────────────────
if not os.path.exists(MODEL_PATH):
    print("[TRACKER] Descargando modelo...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("[TRACKER] Descargado")

# ─── DETECTOR MEDIAPIPE ──────────────────────────────
base_opts = python.BaseOptions(model_asset_path=MODEL_PATH)
opts = vision.HandLandmarkerOptions(
    base_options=base_opts,
    num_hands=NUM_HANDS,
    min_hand_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.VIDEO,
)
detector = vision.HandLandmarker.create_from_options(opts)

# ─── WORKER DB ───────────────────────────────────────
db = DBWorker()
db.start()

# ─── CAMARA ──────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

conexiones = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
]

start_time = time.time()
ultimo_estado = (0,0,0,0,0)
ultimo_envio = 0

print("\n=== INICIADO ===")
print("1-5: cambiar nivel | q: salir\n")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key in [ord(str(i)) for i in range(1, 6)]:
            NIVEL = int(chr(key))
            print(f"[NIVEL] {NIVEL}")

        ts = int((time.time() - start_time) * 1000)
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect_for_video(mp_img, ts)

        pg = i = m = a = mn = 0

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]
            mano = result.handedness[0][0].category_name

            if mano == "Right":
                pg = 1 if lm[4].x < lm[3].x else 0
            else:
                pg = 1 if lm[4].x > lm[3].x else 0

            i  = 1 if lm[8].y  < lm[6].y  else 0
            m  = 1 if lm[12].y < lm[10].y else 0
            a  = 1 if lm[16].y < lm[14].y else 0
            mn = 1 if lm[20].y < lm[18].y else 0

            coords = [(int(l.x * w), int(l.y * h)) for l in lm]
            for a_, b_ in conexiones:
                cv2.line(frame, coords[a_], coords[b_], (255, 0, 0), 2)
            for pt in coords:
                cv2.circle(frame, pt, 4, (0, 255, 0), -1)
            cv2.putText(frame, mano, (coords[0][0]-30, coords[0][1]+30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        estado = (pg, i, m, a, mn)
        if estado != ultimo_estado or (ts - ultimo_envio >= HEARTBEAT_MS):
            db.send(NIVEL, pg, i, m, a, mn)
            ultimo_envio = ts
            if estado != ultimo_estado:
                print(f"[DB] N{NIVEL} P:{pg} I:{i} M:{m} A:{a} Mn:{mn}")
                ultimo_estado = estado

        cv2.rectangle(frame, (10,10), (320,180), (0,0,0), -1)
        cv2.putText(frame, f"NIVEL: {NIVEL}", (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        for j, (nom, val) in enumerate([("Pulgar",pg),("Indice",i),("Medio",m),("Anular",a),("Menique",mn)]):
            color = (0,255,0) if val else (0,0,255)
            cv2.putText(frame, f"{nom}: {'1' if val else '0'}", (20, 70+j*20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        cv2.imshow("DB Finger Tracker", frame)

finally:
    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    db.stop()
    print("[TRACKER] Finalizado")
