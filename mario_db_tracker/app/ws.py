import time
import json
import base64

import cv2
import numpy as np
import mediapipe as mp

from . import hand_tracking as ht


def register_ws(sock, db_worker, config):
    """Register WebSocket route on the Flask-Sock instance."""

    @sock.route('/ws')
    def ws_handler(ws):
        detector = ht.create_detector(config.MODEL_PATH, config.NUM_HANDS)
        start_time = time.time()
        ultimo_estado = (0, 0, 0, 0, 0)
        ultimo_envio = 0
        sens = [50, 50, 50, 50, 50]
        finger_state = [0, 0, 0, 0, 0]
        nivel = 1
        session_id = None
        send_frame = False  # Don't send annotated frames by default (performance)

        print("[WS] Cliente conectado")

        try:
            while True:
                data = ws.receive()
                if data is None:
                    break

                # Handle JSON messages (config, session, etc.)
                if isinstance(data, str):
                    try:
                        msg = json.loads(data)
                        msg_type = msg.get('type')

                        if msg_type == 'config':
                            sens = [max(0, min(100, s)) for s in msg.get('sensitivity', sens)]
                            print(f"[WS] Sensibilidad actualizada: {sens}")
                            continue

                        if msg_type == 'set_nivel':
                            n = msg.get('nivel', 1)
                            if 1 <= n <= 5:
                                nivel = n
                            continue

                        if msg_type == 'start_session':
                            session_id = msg.get('session_id')
                            print(f"[WS] Sesión iniciada: {session_id}")
                            continue

                        if msg_type == 'end_session':
                            session_id = None
                            print("[WS] Sesión terminada")
                            continue

                        if msg_type == 'set_send_frame':
                            send_frame = bool(msg.get('enabled', False))
                            print(f"[WS] Send frame: {send_frame}")
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
                frame = cv2.flip(frame, 1)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = detector.detect_for_video(mp_img, ts)

                landmarks_data = None

                if result.hand_landmarks:
                    lm = result.hand_landmarks[0]

                    diffs = ht.compute_finger_diffs(lm)
                    finger_state = ht.detect_fingers(diffs, sens, finger_state)

                    # Extract landmark coordinates (lightweight — just numbers)
                    landmarks_data = [[round(l.x, 4), round(l.y, 4), round(l.z, 4)] for l in lm]

                    # Only draw on frame if client wants it
                    if send_frame:
                        coords = ht.draw_landmarks(frame, lm)
                        mano = result.handedness[0][0].category_name
                        cv2.putText(frame, mano, (coords[0][0] - 30, coords[0][1] + 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                else:
                    finger_state = [0, 0, 0, 0, 0]

                # DB logging — only on state change
                estado = tuple(finger_state)
                if estado != ultimo_estado:
                    db_worker.send_legacy(nivel, *finger_state)

                    if session_id and landmarks_data:
                        db_worker.send_events_batch(session_id, finger_state, landmarks_data)

                    ultimo_estado = estado

                # Build response — only include frame if requested
                response = {
                    "fingers": finger_state,
                    "nivel": nivel,
                }
                # Always send landmark coords (lightweight, ~500 bytes)
                if landmarks_data:
                    response["lm"] = landmarks_data
                if send_frame:
                    ht.draw_hud(frame, nivel, finger_state)
                    ret_jpg, jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    if ret_jpg:
                        response["frame"] = base64.b64encode(jpg.tobytes()).decode('ascii')

                ws.send(json.dumps(response))

        except Exception as e:
            print(f"[WS] Desconectado: {e}")
        finally:
            detector.close()
            print("[WS] Cliente desconectado")
