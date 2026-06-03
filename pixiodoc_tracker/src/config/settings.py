import os


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 5432))
    DB_NAME = os.environ.get('DB_NAME', 'mario_db')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')

    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

    MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
    MODEL_PATH = os.environ.get('MODEL_PATH', 'hand_landmarker.task')
    NUM_HANDS = 1

    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'templates')
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'static')
