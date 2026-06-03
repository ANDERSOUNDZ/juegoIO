from functools import wraps
from flask import jsonify, abort
from flask_login import current_user
from src.domain.exceptions import DomainError


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)
            if current_user.role not in roles:
                return jsonify(error='No tienes permisos para esta acción'), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error='Recurso no encontrado'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(error='No tienes permisos para esta acción'), 403

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error='Error interno del servidor'), 500

    @app.errorhandler(DomainError)
    def domain_error(e):
        return jsonify(error=str(e)), 400
