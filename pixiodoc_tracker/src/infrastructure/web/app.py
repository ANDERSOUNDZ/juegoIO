import os
from flask import Flask
from jinja2 import FileSystemLoader, ChoiceLoader
from sqlalchemy import text as sa_text

from src.infrastructure.web.config import FlaskConfig
from src.infrastructure.persistence.models import db
from src.infrastructure.persistence.seed_data import SEED_SQL


def _run_migrations(app):
    """Run idempotent DB migrations on startup."""
    with app.app_context():
        try:
            db.session.execute(sa_text("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'roles' AND column_name = 'id'
                    ) THEN
                        CREATE TABLE IF NOT EXISTS roles (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(30) UNIQUE NOT NULL,
                            description TEXT
                        );
                        INSERT INTO roles (name, description) VALUES
                            ('admin', 'Acceso total al sistema'),
                            ('therapist', 'Gestión de pacientes y sesiones'),
                            ('viewer', 'Solo lectura de dashboards y reportes')
                        ON CONFLICT (name) DO NOTHING;
                    END IF;
                END $$;
            """))
            db.session.execute(sa_text("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'users' AND column_name = 'role_id'
                    ) THEN
                        ALTER TABLE users ADD COLUMN role_id INT REFERENCES roles(id);
                    END IF;
                END $$;
            """))
            db.session.commit()

            # ─── Seed default games/sprites (idempotente) ───
            # Cada INSERT tiene WHERE NOT EXISTS, solo inserta lo que falta
            db.session.execute(sa_text(SEED_SQL))
            db.session.commit()
            print('[MIGRACION] Juegos y sprites por defecto sincronizados')

            print('[MIGRACION] Base de datos actualizada correctamente')
        except Exception as e:
            db.session.rollback()
            print(f'[MIGRACION] Warning (no crítico): {e}')


def create_app(settings=None, db_worker=None):
    app = Flask(
        __name__,
        template_folder=settings.TEMPLATE_FOLDER,
        static_folder=settings.STATIC_FOLDER,
    )
    app.config.from_object(FlaskConfig)

    # ─── Add games/ as additional template folder ───
    games_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'games')
    if os.path.isdir(games_dir):
        app.jinja_loader = ChoiceLoader([
            FileSystemLoader(games_dir),
            app.jinja_loader,
        ])

    db.init_app(app)
    _run_migrations(app)

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

    # ─── Serve game assets from /games/ as /static/games/ ───
    games_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'games')
    if os.path.isdir(games_dir):
        from flask import Blueprint
        games_static = Blueprint('games_static', __name__,
                                 static_url_path='/static/games',
                                 static_folder=games_dir)
        app.register_blueprint(games_static)

    if db_worker:
        from .controllers.auth import init_login_manager
        init_login_manager(app)

    from .middleware import register_error_handlers
    register_error_handlers(app)

    return app
