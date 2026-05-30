from src.config.settings import Settings
from src.infrastructure.persistence.db_worker import DBWorker


def create_db_worker(settings: Settings) -> DBWorker:
    worker = DBWorker(
        host=settings.DB_HOST, port=settings.DB_PORT,
        database=settings.DB_NAME, user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    worker.start()
    return worker
