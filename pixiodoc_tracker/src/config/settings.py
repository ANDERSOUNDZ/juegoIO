import os
from urllib.parse import urlparse


def _parse_db_url(url):
    p = urlparse(url)
    return {
        'host': p.hostname or 'localhost',
        'port': p.port or 5432,
        'name': (p.path or '/mario_db').lstrip('/'),
        'user': p.username or 'postgres',
        'password': p.password or 'admin',
    }


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    _db_url = os.environ.get('DATABASE_URL', '')
    if _db_url:
        _parsed = _parse_db_url(_db_url)
        DB_HOST = _parsed['host']
        DB_PORT = _parsed['port']
        DB_NAME = _parsed['name']
        DB_USER = _parsed['user']
        DB_PASSWORD = _parsed['password']
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_PORT = int(os.environ.get('DB_PORT', 5432))
        DB_NAME = os.environ.get('DB_NAME', 'mario_db')
        DB_USER = os.environ.get('DB_USER', 'postgres')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')
        SQLALCHEMY_DATABASE_URI = (
            f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        )

    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'templates')
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'static')
