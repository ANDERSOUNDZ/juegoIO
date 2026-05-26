from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import db, Sprite

sprites_bp = Blueprint('sprites_api', __name__, url_prefix='/api/sprites')


def sprite_to_dict(s):
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
    q = Sprite.query
    category = request.args.get('category')
    if category:
        q = q.filter_by(category=category)
    sprites = q.order_by(Sprite.created_at.desc()).all()
    return jsonify([sprite_to_dict(s) for s in sprites])


@sprites_bp.route('', methods=['POST'])
@login_required
def create_sprite():
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    for field in ('name', 'category', 'type', 'width', 'height'):
        if not data.get(field):
            return jsonify(error=f"{field} es requerido"), 400

    if data['type'] == 'pixelmap' and not data.get('data'):
        return jsonify(error="data es requerido para tipo pixelmap"), 400
    if data['type'] == 'image' and not data.get('image_url'):
        return jsonify(error="image_url es requerido para tipo image"), 400

    s = Sprite(
        name=data['name'],
        category=data['category'],
        type=data['type'],
        width=data['width'],
        height=data['height'],
        data=data.get('data'),
        image_url=data.get('image_url'),
        frame_count=data.get('frame_count', 1),
        created_by=current_user.id,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(sprite_to_dict(s)), 201


@sprites_bp.route('/<int:sid>', methods=['GET'])
@login_required
def get_sprite(sid):
    s = Sprite.query.get_or_404(sid)
    return jsonify(sprite_to_dict(s))


@sprites_bp.route('/<int:sid>', methods=['PUT'])
@login_required
def update_sprite(sid):
    s = Sprite.query.get_or_404(sid)
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    for field in ('name', 'category', 'type', 'width', 'height', 'data', 'image_url', 'frame_count'):
        if field in data:
            setattr(s, field, data[field])

    db.session.commit()
    return jsonify(sprite_to_dict(s))


@sprites_bp.route('/<int:sid>', methods=['DELETE'])
@login_required
def delete_sprite(sid):
    s = Sprite.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify(ok=True)


@sprites_bp.route('/batch', methods=['POST'])
@login_required
def get_batch():
    """Get multiple sprites by IDs. Used by game-loader to resolve sprite_ids."""
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    if not ids:
        return jsonify([])
    sprites = Sprite.query.filter(Sprite.id.in_(ids)).all()
    return jsonify([sprite_to_dict(s) for s in sprites])
