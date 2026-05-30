from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.application.sprite_service import SpriteService
from src.infrastructure.persistence.repositories import SpriteRepository
from src.domain.exceptions import NotFoundError, ValidationError

sprites_bp = Blueprint('sprites_api', __name__, url_prefix='/api/sprites')
_service = SpriteService(SpriteRepository())


def _sprite_to_dict(s):
    return dict(
        id=s.id, name=s.name, category=s.category, type=s.type,
        width=s.width, height=s.height,
        data=s.data, image_url=s.image_url,
        frame_count=s.frame_count,
        created_by=s.created_by,
        created_at=s.created_at.isoformat() if s.created_at else None,
    )


@sprites_bp.route('', methods=['GET'])
@login_required
def list_sprites():
    category = request.args.get('category')
    sprites = _service.list_all(category)
    return jsonify([_sprite_to_dict(s) for s in sprites])


@sprites_bp.route('', methods=['POST'])
@login_required
def create_sprite():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        s = _service.create(
            name=data.get('name', ''), category=data.get('category', ''),
            type=data.get('type', 'pixelmap'),
            width=data.get('width', 0), height=data.get('height', 0),
            data=data.get('data'), image_url=data.get('image_url'),
            frame_count=data.get('frame_count', 1),
            created_by=current_user.id,
        )
        return jsonify(_sprite_to_dict(s)), 201
    except ValidationError as e:
        return jsonify(error=str(e)), 400


@sprites_bp.route('/<int:sid>', methods=['GET'])
@login_required
def get_sprite(sid):
    try:
        s = _service.get_by_id(sid)
        return jsonify(_sprite_to_dict(s))
    except NotFoundError:
        return jsonify(error='Sprite no encontrado'), 404


@sprites_bp.route('/<int:sid>', methods=['PUT'])
@login_required
def update_sprite(sid):
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        s = _service.update(sid, data)
        return jsonify(_sprite_to_dict(s))
    except NotFoundError:
        return jsonify(error='Sprite no encontrado'), 404


@sprites_bp.route('/<int:sid>', methods=['DELETE'])
@login_required
def delete_sprite(sid):
    try:
        _service.delete(sid)
        return jsonify(ok=True)
    except NotFoundError:
        return jsonify(error='Sprite no encontrado'), 404


@sprites_bp.route('/batch', methods=['POST'])
@login_required
def get_batch():
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    sprites = _service.get_batch(ids)
    return jsonify([_sprite_to_dict(s) for s in sprites])
