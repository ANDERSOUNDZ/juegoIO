import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import Settings
from src.infrastructure.di import create_db_worker
from src.infrastructure.web.app import create_app

settings = Settings()
db_worker = create_db_worker(settings)

app = create_app(settings=settings, db_worker=db_worker)

if __name__ == '__main__':
    print("\n[SERVER] Abre http://localhost:5000 en tu navegador")
    print("[SERVER] La camara se activa en el CLIENTE (navegador)")
    print("[SERVER] Presiona Ctrl+C para detener\n")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    finally:
        db_worker.stop()
