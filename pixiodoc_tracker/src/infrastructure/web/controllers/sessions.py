from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.application.session_service import SessionService
from src.infrastructure.persistence.repositories import (
    SessionRepository, FingerEventRepository,
    GameRepository, PatientRepository,
)
from src.domain.exceptions import NotFoundError
from src.infrastructure.web.middleware import role_required

sessions_bp = Blueprint('sessions_api', __name__, url_prefix='/api/sessions')
_service = SessionService(
    SessionRepository(), FingerEventRepository(),
    GameRepository(), PatientRepository(),
)


def _session_to_dict(s):
    game = GameRepository().find_by_id(s.game_id) if s.game_id else None
    return dict(
        id=s.id, patient_id=s.patient_id, game_id=s.game_id,
        user_id=s.user_id,
        started_at=s.started_at.isoformat() if s.started_at else None,
        ended_at=s.ended_at.isoformat() if s.ended_at else None,
        score=s.score, metadata=s.metadata_,
        game_name=game.name if game else None,
    )


@sessions_bp.route('', methods=['GET'])
@login_required
def list_sessions():
    patient_id = request.args.get('patient_id', type=int)
    game_id = request.args.get('game_id', type=int)
    user_role = current_user.role_rel.name if current_user.role_rel else 'therapist'
    sessions = _service.list_by_user(current_user.id, patient_id, game_id, user_role=user_role)
    return jsonify([_session_to_dict(s) for s in sessions])


@sessions_bp.route('', methods=['POST'])
@login_required
@role_required(1, 2, 3)
def create_session():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        s = _service.create(
            patient_id=data.get('patient_id'),
            game_id=data.get('game_id'),
            user_id=current_user.id,
            metadata=data.get('metadata'),
        )
        return jsonify(_session_to_dict(s)), 201
    except NotFoundError as e:
        return jsonify(error=str(e)), 404


@sessions_bp.route('/<int:sid>/end', methods=['PUT'])
@login_required
@role_required(1, 2, 3)
def end_session(sid):
    data = request.get_json() or {}
    try:
        s = _service.end(sid, score=data.get('score'), metadata=data.get('metadata'))
        return jsonify(_session_to_dict(s))
    except NotFoundError:
        return jsonify(error='Sesión no encontrada'), 404


@sessions_bp.route('/<int:sid>', methods=['GET'])
@login_required
def get_session(sid):
    try:
        s = _service.get_by_id(sid)
        return jsonify(_session_to_dict(s))
    except NotFoundError:
        return jsonify(error='Sesión no encontrada'), 404


@sessions_bp.route('/<int:sid>/events', methods=['POST'])
@login_required
def post_events(sid):
    data = request.get_json()
    if not data or not data.get('events'):
        return jsonify(ok=True)
    events = data['events']
    db_worker = sessions_bp.db_worker
    if not db_worker:
        return jsonify(error='No db_worker configured'), 500
    rows = []
    for e in events:
        rows.append((
            sid,
            e.get('finger_index'),
            e.get('state'),
            e.get('landmark_x'),
            e.get('landmark_y'),
            e.get('landmark_z'),
        ))
    if rows:
        db_worker.enqueue_rows(rows)
    return jsonify(ok=True)


@sessions_bp.route('/<int:sid>/events', methods=['GET'])
@login_required
def get_events(sid):
    try:
        events = _service.get_events(sid)
        return jsonify([
            dict(
                finger_index=e.finger_index, state=e.state,
                landmark_x=e.landmark_x, landmark_y=e.landmark_y,
                landmark_z=e.landmark_z,
                timestamp=e.timestamp.isoformat() if e.timestamp else None,
            )
            for e in events
        ])
    except NotFoundError:
        return jsonify(error='Sesión no encontrada'), 404


@sessions_bp.route('/<int:sid>/report', methods=['GET'])
@login_required
def get_report(sid):
    try:
        report = _service.get_report(sid)
        return jsonify(**report)
    except NotFoundError:
        return jsonify(error='Sesión no encontrada'), 404
