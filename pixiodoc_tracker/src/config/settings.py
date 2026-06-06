import os
from urllib.parse import urlparse


def _resolve_db():
    url = os.environ.get('DATABASE_URL', '')
    if url:
        p = urlparse(url)
        return dict(
            uri=url,
            host=p.hostname or 'localhost',
            port=p.port or 5432,
            name=(p.path or '/mario_db').lstrip('/'),
            user=p.username or 'postgres',
            password=p.password or 'admin',
        )
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', 5432))
    name = os.environ.get('DB_NAME', 'mario_db')
    user = os.environ.get('DB_USER', 'postgres')
    password = os.environ.get('DB_PASSWORD', 'admin')
    return dict(
        uri=f'postgresql://{user}:{password}@{host}:{port}/{name}',
        host=host, port=port, name=name, user=user, password=password,
    )


_db = _resolve_db()


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    SQLALCHEMY_DATABASE_URI = _db['uri']
    DB_HOST     = _db['host']
    DB_PORT     = _db['port']
    DB_NAME     = _db['name']
    DB_USER     = _db['user']
    DB_PASSWORD = _db['password']

    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'templates')
    STATIC_FOLDER   = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'static')
