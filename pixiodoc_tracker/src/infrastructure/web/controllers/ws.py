import json


def register_ws(sock, db_worker):
    @sock.route('/ws')
    def ws_handler(ws):
        session_id = None
        sens = [50, 50, 50, 50, 50]

        print('[WS] Cliente conectado')

        try:
            while True:
                data = ws.receive()
                if data is None:
                    break

                if isinstance(data, str):
                    try:
                        msg = json.loads(data)
                    except (json.JSONDecodeError, ValueError):
                        continue

                    msg_type = msg.get('type')

                    if msg_type == 'config':
                        sens = [max(0, min(100, s)) for s in msg.get('sensitivity', sens)]
                        print(f'[WS] Sensibilidad: {sens}')
                        continue

                    if msg_type == 'start_session':
                        session_id = msg.get('session_id')
                        print(f'[WS] Sesión iniciada: {session_id}')
                        continue

                    if msg_type == 'end_session':
                        session_id = None
                        print('[WS] Sesión terminada')
                        continue

                    if msg_type == 'finger_update':
                        if session_id and msg.get('fingers'):
                            db_worker.send_events_batch(
                                session_id,
                                msg['fingers'],
                                msg.get('landmarks'),
                            )
                        continue

        except Exception as e:
            print(f'[WS] Desconectado: {e}')
        finally:
            print('[WS] Cliente desconectado')
