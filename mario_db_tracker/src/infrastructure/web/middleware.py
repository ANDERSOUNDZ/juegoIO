from flask import jsonify
from src.domain.exceptions import DomainError


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error='Recurso no encontrado'), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error='Error interno del servidor'), 500

    @app.errorhandler(DomainError)
    def domain_error(e):
        return jsonify(error=str(e)), 400
