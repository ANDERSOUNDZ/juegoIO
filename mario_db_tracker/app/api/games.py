from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import db, Game, PlayerGameConfig
from datetime import datetime, timezone

games_bp = Blueprint('games_api', __name__, url_prefix='/api/games')


def game_to_dict(g, include_config=False):
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
def list_games():
    games = Game.query.order_by(Game.created_at.desc()).all()
    return jsonify([game_to_dict(g) for g in games])


@games_bp.route('', methods=['POST'])
@login_required
def create_game():
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    for field in ('name', 'game_type', 'config'):
        if not data.get(field):
            return jsonify(error=f"{field} es requerido"), 400

    g = Game(
        name=data['name'],
        description=data.get('description'),
        game_type=data['game_type'],
        thumbnail_url=data.get('thumbnail_url'),
        config=data['config'],
        created_by=current_user.id,
    )
    db.session.add(g)
    db.session.commit()
    return jsonify(game_to_dict(g, include_config=True)), 201


@games_bp.route('/<int:gid>', methods=['GET'])
@login_required
def get_game(gid):
    g = Game.query.get_or_404(gid)
    return jsonify(game_to_dict(g, include_config=True))


@games_bp.route('/<int:gid>', methods=['PUT'])
@login_required
def update_game(gid):
    g = Game.query.get_or_404(gid)
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    for field in ('name', 'description', 'game_type', 'thumbnail_url', 'config'):
        if field in data:
            setattr(g, field, data[field])

    db.session.commit()
    return jsonify(game_to_dict(g, include_config=True))


@games_bp.route('/<int:gid>', methods=['DELETE'])
@login_required
def delete_game(gid):
    g = Game.query.get_or_404(gid)
    db.session.delete(g)
    db.session.commit()
    return jsonify(ok=True)


@games_bp.route('/<int:gid>/config', methods=['GET'])
@login_required
def get_game_config(gid):
    g = Game.query.get_or_404(gid)
    return jsonify(g.config)


# ─── Player-specific config per game ────────────────────────────

@games_bp.route('/<int:gid>/player-config/<int:pid>', methods=['GET'])
@login_required
def get_player_game_config(gid, pid):
    """Get controls config for a patient+game. Falls back to game defaults."""
    g = Game.query.get_or_404(gid)
    pgc = PlayerGameConfig.query.filter_by(patient_id=pid, game_id=gid).first()

    if pgc:
        return jsonify(
            sensitivities=pgc.sensitivities,
            finger_map=pgc.finger_map,
            is_custom=True,
        )

    # No custom config → return game defaults
    game_controls = g.config.get('controls', {})
    return jsonify(
        sensitivities=[50, 50, 50, 50, 50],
        finger_map=game_controls.get('fingerMap', {"0": "jump", "1": "right", "2": "left", "3": "none", "4": "none"}),
        is_custom=False,
    )


@games_bp.route('/<int:gid>/player-config/<int:pid>', methods=['PUT'])
@login_required
def save_player_game_config(gid, pid):
    """Save controls config for a patient+game."""
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    pgc = PlayerGameConfig.query.filter_by(patient_id=pid, game_id=gid).first()
    if pgc:
        if 'sensitivities' in data:
            pgc.sensitivities = data['sensitivities']
        if 'finger_map' in data:
            pgc.finger_map = data['finger_map']
        pgc.updated_at = datetime.now(timezone.utc)
    else:
        pgc = PlayerGameConfig(
            patient_id=pid,
            game_id=gid,
            sensitivities=data.get('sensitivities', [50, 50, 50, 50, 50]),
            finger_map=data.get('finger_map', {"0": "jump", "1": "right", "2": "left", "3": "none", "4": "none"}),
        )
        db.session.add(pgc)

    db.session.commit()
    return jsonify(sensitivities=pgc.sensitivities, finger_map=pgc.finger_map, ok=True)
