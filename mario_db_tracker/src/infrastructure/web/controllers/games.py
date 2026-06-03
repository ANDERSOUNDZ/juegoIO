from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.application.game_service import GameService
from src.infrastructure.persistence.repositories import GameRepository, PlayerGameConfigRepository
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.web.middleware import role_required

games_bp = Blueprint('games_api', __name__, url_prefix='/api/games')
_service = GameService(GameRepository(), PlayerGameConfigRepository())


def _game_to_dict(g, include_config=False):
    d = dict(
        id=g.id, name=g.name, description=g.description,
        game_type=g.game_type, thumbnail_url=g.thumbnail_url,
        created_by=g.created_by,
        created_at=g.created_at.isoformat() if g.created_at else None,
    )
    if include_config:
        d['config'] = g.config
    return d


@games_bp.route('', methods=['GET'])
@login_required
@role_required('admin', 'therapist')
def list_games():
    games = _service.list_all()
    return jsonify([_game_to_dict(g) for g in games])


@games_bp.route('', methods=['POST'])
@login_required
@role_required('admin')
def create_game():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        g = _service.create(
            name=data.get('name', ''), game_type=data.get('game_type', ''),
            config=data.get('config', {}), description=data.get('description'),
            thumbnail_url=data.get('thumbnail_url'), created_by=current_user.id,
        )
        return jsonify(_game_to_dict(g, include_config=True)), 201
    except ValidationError as e:
        return jsonify(error=str(e)), 400


@games_bp.route('/<int:gid>', methods=['GET'])
@login_required
@role_required('admin', 'therapist')
def get_game(gid):
    try:
        g = _service.get_by_id(gid)
        return jsonify(_game_to_dict(g, include_config=True))
    except NotFoundError:
        return jsonify(error='Juego no encontrado'), 404


@games_bp.route('/<int:gid>', methods=['PUT'])
@login_required
@role_required('admin')
def update_game(gid):
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        g = _service.update(gid, data)
        return jsonify(_game_to_dict(g, include_config=True))
    except NotFoundError:
        return jsonify(error='Juego no encontrado'), 404


@games_bp.route('/<int:gid>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_game(gid):
    try:
        _service.delete(gid)
        return jsonify(ok=True)
    except NotFoundError:
        return jsonify(error='Juego no encontrado'), 404


@games_bp.route('/<int:gid>/config', methods=['GET'])
@login_required
@role_required('admin', 'therapist')
def get_game_config(gid):
    try:
        return jsonify(_service.get_config(gid))
    except NotFoundError:
        return jsonify(error='Juego no encontrado'), 404


@games_bp.route('/<int:gid>/player-config/<int:pid>', methods=['GET'])
@login_required
@role_required('admin', 'therapist')
def get_player_game_config(gid, pid):
    try:
        return jsonify(_service.get_player_config(gid, pid))
    except NotFoundError:
        return jsonify(error='Juego no encontrado'), 404


@games_bp.route('/<int:gid>/player-config/<int:pid>', methods=['PUT'])
@login_required
@role_required('admin', 'therapist')
def save_player_game_config(gid, pid):
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        result = _service.save_player_config(gid, pid, data)
        return jsonify(**result, ok=True)
    except NotFoundError:
        return jsonify(error='Juego no encontrado'), 404
