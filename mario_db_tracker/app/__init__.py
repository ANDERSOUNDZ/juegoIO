from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_sock import Sock

from .config import Config
from .models import db, User
from .db_worker import DBWorker
from .hand_tracking import ensure_model


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    sock = Sock(app)

    # DB Worker (high-freq inserts)
    db_worker = DBWorker(
        host=Config.DB_HOST, port=Config.DB_PORT,
        database=Config.DB_NAME, user=Config.DB_USER, password=Config.DB_PASSWORD,
    )
    db_worker.start()
    app.db_worker = db_worker

    # Ensure MediaPipe model
    ensure_model(Config.MODEL_URL, Config.MODEL_PATH)

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .api.patients import patients_bp
    app.register_blueprint(patients_bp)

    from .api.games import games_bp
    app.register_blueprint(games_bp)

    from .api.sessions import sessions_bp
    app.register_blueprint(sessions_bp)

    from .api.sensitivity import sensitivity_bp
    app.register_blueprint(sensitivity_bp)

    from .api.sprites import sprites_bp
    app.register_blueprint(sprites_bp)

    # Register WebSocket
    from .ws import register_ws
    register_ws(sock, db_worker, Config)

    # Main routes
    from . import routes
    app.register_blueprint(routes.main_bp)

    return app
