from src.config.settings import Settings


class FlaskConfig:
    SECRET_KEY = Settings.SECRET_KEY
    SQLALCHEMY_DATABASE_URI = Settings.SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
