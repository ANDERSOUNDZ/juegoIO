from flask import Flask

from src.infrastructure.web.config import FlaskConfig
from src.infrastructure.persistence.models import db


def create_app(settings=None, db_worker=None):
    app = Flask(
        __name__,
        template_folder=settings.TEMPLATE_FOLDER,
        static_folder=settings.STATIC_FOLDER,
    )
    app.config.from_object(FlaskConfig)

    db.init_app(app)

    from .controllers.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .controllers.patients import patients_bp
    app.register_blueprint(patients_bp)

    from .controllers.games import games_bp
    app.register_blueprint(games_bp)

    from .controllers.sessions import sessions_bp
    sessions_bp.db_worker = db_worker
    app.register_blueprint(sessions_bp)

    from .controllers.sensitivity import sensitivity_bp
    app.register_blueprint(sensitivity_bp)

    from .controllers.sprites import sprites_bp
    app.register_blueprint(sprites_bp)

    from .controllers.analytics import analytics_bp
    app.register_blueprint(analytics_bp)

    from .controllers.pages import main_bp
    app.register_blueprint(main_bp)

    if db_worker:
        from .controllers.auth import init_login_manager
        init_login_manager(app)

    from .middleware import register_error_handlers
    register_error_handlers(app)

    return app
