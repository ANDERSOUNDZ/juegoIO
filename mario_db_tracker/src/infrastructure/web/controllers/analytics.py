from flask import Blueprint, jsonify, render_template, make_response
from flask_login import login_required

from src.application.analytics_service import AnalyticsService
from src.infrastructure.persistence.repositories import (
    FingerEventRepository, SessionRepository,
    PatientRepository, GameRepository,
)
from src.domain.exceptions import NotFoundError
from src.infrastructure.web.middleware import role_required

analytics_bp = Blueprint('analytics_api', __name__, url_prefix='/api/sessions')
_service = AnalyticsService(
    FingerEventRepository(), SessionRepository(),
    PatientRepository(), GameRepository(),
)


@analytics_bp.route('/<int:sid>/analytics', methods=['GET'])
@login_required
def get_analytics(sid):
    try:
        prev_id = _get_previous_session_id(sid)
        data = _service.get_analytics(sid, previous_session_id=prev_id)
        return jsonify(**data)
    except NotFoundError as e:
        return jsonify(error=str(e)), 404


@analytics_bp.route('/<int:sid>/report/pdf', methods=['GET'])
@login_required
def get_pdf(sid):
    try:
        data = _service.get_pdf_data(sid)
    except NotFoundError as e:
        return jsonify(error=str(e)), 404

    try:
        from weasyprint import HTML
        html = render_template('report_pdf.html', **data)
        pdf = HTML(string=html).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=reporte_sesion_{sid}.pdf'
        return response
    except ImportError:
        return jsonify(error='PDF no disponible en este entorno. Use Docker para generar PDFs.'), 501


def _get_previous_session_id(session_id: int):
    """Find the most recent session before this one for the same patient."""
    from src.infrastructure.persistence.repositories import SessionRepository
    repo = SessionRepository()
    session = repo.find_by_id(session_id)
    if not session:
        return None
    # Use user_role='admin' to find all sessions for this patient regardless of who created them
    all_sessions = repo.find_by_user_id(session.user_id, patient_id=session.patient_id, user_role='admin')
    ids = sorted([s.id for s in all_sessions if s.id < session_id], reverse=True)
    return ids[0] if ids else None
