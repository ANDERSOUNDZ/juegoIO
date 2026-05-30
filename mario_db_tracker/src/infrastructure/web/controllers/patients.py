from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.application.patient_service import PatientService
from src.infrastructure.persistence.repositories import (
    PatientRepository, PatientSensitivityRepository,
    SensitivityHistoryRepository, SensitivityPresetRepository,
)
from src.domain.exceptions import NotFoundError, ValidationError

patients_bp = Blueprint('patients_api', __name__, url_prefix='/api/patients')
_service = PatientService(
    PatientRepository(), PatientSensitivityRepository(),
    SensitivityHistoryRepository(), SensitivityPresetRepository(),
)


def _patient_to_dict(p):
    ps = PatientSensitivityRepository().find_by_patient_id(p.id)
    return dict(
        id=p.id, name=p.name, age=p.age,
        diagnosis=p.diagnosis, notes=p.notes,
        user_id=p.user_id,
        created_at=p.created_at.isoformat() if p.created_at else None,
        sensitivity=ps.sensitivities if ps else None,
    )


@patients_bp.route('', methods=['GET'])
@login_required
def list_patients():
    patients = _service.list_by_user(current_user.id)
    return jsonify([_patient_to_dict(p) for p in patients])


@patients_bp.route('', methods=['POST'])
@login_required
def create_patient():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify(error='name es requerido'), 400
    p = _service.create(
        user_id=current_user.id, name=data['name'],
        age=data.get('age'), diagnosis=data.get('diagnosis'), notes=data.get('notes'),
    )
    return jsonify(_patient_to_dict(p)), 201


@patients_bp.route('/<int:pid>', methods=['GET'])
@login_required
def get_patient(pid):
    try:
        p = _service.get_by_id(pid)
        return jsonify(_patient_to_dict(p))
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404


@patients_bp.route('/<int:pid>', methods=['PUT'])
@login_required
def update_patient(pid):
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        p = _service.update(pid, data)
        return jsonify(_patient_to_dict(p))
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404


@patients_bp.route('/<int:pid>', methods=['DELETE'])
@login_required
def delete_patient(pid):
    try:
        _service.delete(pid)
        return jsonify(ok=True)
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404


@patients_bp.route('/<int:pid>/sensitivity', methods=['GET'])
@login_required
def get_sensitivity(pid):
    try:
        result = _service.get_sensitivity(pid)
        return jsonify(**result)
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404


@patients_bp.route('/<int:pid>/sensitivity', methods=['PUT'])
@login_required
def update_sensitivity(pid):
    data = request.get_json()
    if not data or 'sensitivities' not in data:
        return jsonify(error='sensitivities es requerido'), 400
    try:
        result = _service.update_sensitivity(
            pid, data['sensitivities'],
            preset_id=data.get('preset_id'),
            reason=data.get('reason'),
            changed_by=current_user.id,
        )
        return jsonify(**result)
    except (NotFoundError, ValidationError) as e:
        return jsonify(error=str(e)), 400


@patients_bp.route('/<int:pid>/sensitivity/history', methods=['GET'])
@login_required
def sensitivity_history(pid):
    try:
        history = _service.get_sensitivity_history(pid)
        return jsonify([
            dict(
                id=h.id,
                old_sensitivities=h.old_sensitivities,
                new_sensitivities=h.new_sensitivities,
                reason=h.reason,
                changed_by=h.changed_by,
                changed_at=h.changed_at.isoformat() if h.changed_at else None,
            )
            for h in history
        ])
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404
