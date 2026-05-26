import queue
import threading
import psycopg2
from psycopg2.extras import execute_values


class DBWorker:
    """Async queue-based worker for high-frequency DB inserts.
    Uses batch inserts for performance."""

    def __init__(self, host, port, database, user, password):
        self.db_config = dict(host=host, port=port, database=database, user=user, password=password)
        self.q = queue.Queue(maxsize=500)
        self.running = False
        self.thread = None
        self.conn = None
        self.cursor = None

    def _connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_config)
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

    def _enqueue(self, item):
        try:
            self.q.put_nowait(item)
        except queue.Full:
            # Drop oldest to make room
            try:
                self.q.get_nowait()
            except queue.Empty:
                pass
            try:
                self.q.put_nowait(item)
            except queue.Full:
                pass

    def send_legacy(self, nivel, pulgar, indice, medio, anular, menique):
        """Insert into control_juego (backward compat)."""
        self._enqueue(('legacy', (nivel, pulgar, indice, medio, anular, menique)))

    def send_events_batch(self, session_id, finger_states, landmarks_data):
        """Queue a single batch item with all 5 finger events."""
        rows = []
        tip_indices = [4, 8, 12, 16, 20]
        for i in range(5):
            tip = tip_indices[i]
            lx = landmarks_data[tip][0] if landmarks_data else None
            ly = landmarks_data[tip][1] if landmarks_data else None
            lz = landmarks_data[tip][2] if landmarks_data else None
            rows.append((session_id, i, finger_states[i], lx, ly, lz))
        self._enqueue(('events_batch', rows))

    def _run(self):
        self._connect()
        while self.running:
            try:
                item = self.q.get(timeout=1)
                if item is None:
                    break

                kind, data = item
                if not (self.conn and self.cursor):
                    self.q.task_done()
                    continue

                try:
                    if kind == 'legacy':
                        n, pg, i, m, a, mn = data
                        self.cursor.execute(
                            "INSERT INTO control_juego (nivel, pulgar, indice, medio, anular, menique) VALUES (%s,%s,%s,%s,%s,%s)",
                            (n, pg, i, m, a, mn),
                        )
                    elif kind == 'events_batch':
                        # Batch insert all finger events in one query
                        execute_values(
                            self.cursor,
                            "INSERT INTO finger_events (session_id, finger_index, state, landmark_x, landmark_y, landmark_z) VALUES %s",
                            data,
                        )
                except Exception as e:
                    print(f"[DB] Error insert: {e}")
                    self._connect()

                self.q.task_done()
            except queue.Empty:
                continue
