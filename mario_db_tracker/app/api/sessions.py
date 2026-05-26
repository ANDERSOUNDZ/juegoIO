from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import db, GameSession, FingerEvent
from datetime import datetime, timezone
from sqlalchemy import func

sessions_bp = Blueprint('sessions_api', __name__, url_prefix='/api/sessions')


def session_to_dict(s):
    return dict(
        id=s.id,
        patient_id=s.patient_id,
        game_id=s.game_id,
        user_id=s.user_id,
        started_at=s.started_at.isoformat() if s.started_at else None,
        ended_at=s.ended_at.isoformat() if s.ended_at else None,
        score=s.score,
        metadata=s.metadata_,
        game_name=s.game.name if s.game else None,
    )


@sessions_bp.route('', methods=['GET'])
@login_required
def list_sessions():
    q = GameSession.query.filter_by(user_id=current_user.id)

    patient_id = request.args.get('patient_id', type=int)
    if patient_id:
        q = q.filter_by(patient_id=patient_id)

    game_id = request.args.get('game_id', type=int)
    if game_id:
        q = q.filter_by(game_id=game_id)

    sessions = q.order_by(GameSession.started_at.desc()).limit(100).all()
    return jsonify([session_to_dict(s) for s in sessions])


@sessions_bp.route('', methods=['POST'])
@login_required
def create_session():
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    if not data.get('patient_id') or not data.get('game_id'):
        return jsonify(error="patient_id y game_id son requeridos"), 400

    s = GameSession(
        patient_id=data['patient_id'],
        game_id=data['game_id'],
        user_id=current_user.id,
        metadata_=data.get('metadata'),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(session_to_dict(s)), 201


@sessions_bp.route('/<int:sid>/end', methods=['PUT'])
@login_required
def end_session(sid):
    s = GameSession.query.get_or_404(sid)
    data = request.get_json() or {}

    s.ended_at = datetime.now(timezone.utc)
    if 'score' in data:
        s.score = data['score']
    if 'metadata' in data:
        s.metadata_ = data['metadata']

    db.session.commit()
    return jsonify(session_to_dict(s))


@sessions_bp.route('/<int:sid>', methods=['GET'])
@login_required
def get_session(sid):
    s = GameSession.query.get_or_404(sid)
    return jsonify(session_to_dict(s))


@sessions_bp.route('/<int:sid>/events', methods=['GET'])
@login_required
def get_events(sid):
    GameSession.query.get_or_404(sid)
    events = FingerEvent.query.filter_by(session_id=sid).order_by(FingerEvent.timestamp).all()
    return jsonify([
        dict(
            finger_index=e.finger_index, state=e.state,
            landmark_x=e.landmark_x, landmark_y=e.landmark_y, landmark_z=e.landmark_z,
            timestamp=e.timestamp.isoformat() if e.timestamp else None,
        )
        for e in events
    ])


@sessions_bp.route('/<int:sid>/report', methods=['GET'])
@login_required
def get_report(sid):
    s = GameSession.query.get_or_404(sid)

    # Activations per finger
    activations = db.session.query(
        FingerEvent.finger_index,
        func.count().label('total'),
        func.sum(FingerEvent.state).label('active_count'),
    ).filter_by(session_id=sid).group_by(FingerEvent.finger_index).all()

    finger_names = ['Pulgar', 'Índice', 'Medio', 'Anular', 'Meñique']
    finger_stats = []
    for row in activations:
        finger_stats.append(dict(
            finger_index=row.finger_index,
            name=finger_names[row.finger_index] if row.finger_index < 5 else f"Dedo {row.finger_index}",
            total_events=row.total,
            active_count=row.active_count or 0,
        ))

    # Movement range per finger
    movement = db.session.query(
        FingerEvent.finger_index,
        func.min(FingerEvent.landmark_x).label('min_x'),
        func.max(FingerEvent.landmark_x).label('max_x'),
        func.min(FingerEvent.landmark_y).label('min_y'),
        func.max(FingerEvent.landmark_y).label('max_y'),
    ).filter_by(session_id=sid).filter(
        FingerEvent.landmark_x.isnot(None)
    ).group_by(FingerEvent.finger_index).all()

    movement_stats = []
    for row in movement:
        movement_stats.append(dict(
            finger_index=row.finger_index,
            range_x=round((row.max_x or 0) - (row.min_x or 0), 4),
            range_y=round((row.max_y or 0) - (row.min_y or 0), 4),
        ))

    # Duration
    duration = None
    if s.started_at and s.ended_at:
        duration = (s.ended_at - s.started_at).total_seconds()

    return jsonify(
        session=session_to_dict(s),
        duration_seconds=duration,
        finger_stats=finger_stats,
        movement_stats=movement_stats,
    )
