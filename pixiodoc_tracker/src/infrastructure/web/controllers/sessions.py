from flask import Blueprint, request, jsonify, render_template
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


@sessions_bp.route('/<int:sid>/analytics', methods=['GET'])
@login_required
def get_analytics(sid):
    try:
        analytics = _service.get_analytics(sid)
        return jsonify(**analytics)
    except NotFoundError:
        return jsonify(error='Sesión no encontrada'), 404


@sessions_bp.route('/<int:sid>/report/pdf', methods=['GET'])
@login_required
def get_report_pdf(sid):
    try:
        report = _service.get_report(sid)
        analytics = _service.get_analytics(sid)
    except NotFoundError:
        return jsonify(error='Sesión no encontrada'), 404

    session = report['session']
    patient = PatientRepository().find_by_id(session.get('patient_id')) if session.get('patient_id') else None

    finger_names = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Menique']
    act_map = {f['finger_index']: f['active_count'] for f in report['finger_stats']}
    finger_rows = []
    for i in range(5):
        m = analytics['metrics'].get(str(i), {})
        has = m.get('has_data', False)
        rom_val = m.get('rom', 0.0)
        fat_val = m.get('fatigue', 0)
        trem_val = m.get('tremor', 0.0)
        alert = (rom_val < 0.05 and has) or fat_val > 25 or trem_val > 0.015
        finger_rows.append({
            'name': finger_names[i],
            'alert': alert,
            'rom': round(rom_val, 4) if has else '-',
            'reaction': '-',
            'fatigue': f'{fat_val}%' if has else '-',
            'tremor': round(trem_val, 4) if has else '-',
            'activations': act_map.get(i, 0),
        })

    indep = analytics['metrics'].get('independence', {'score': 0, 'issues': [], 'status': '-'})

    return render_template('report_pdf.html',
        patient_name=patient.name if patient else 'Paciente',
        patient_age=patient.age if patient and patient.age else '-',
        patient_diagnosis=patient.diagnosis if patient and patient.diagnosis else '-',
        game_name=session.get('game_name') or '-',
        date=session.get('started_at') or '',
        duration=report.get('duration_seconds'),
        functional_score=analytics.get('functional_score', 0),
        previous_session=analytics.get('previous_session'),
        finger_rows=finger_rows,
        independence=indep,
        interpretation=analytics.get('interpretation', ''),
    )
