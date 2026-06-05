from datetime import date, datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.application.patient_service import PatientService
from src.infrastructure.persistence.repositories import (
    PatientRepository, PatientSensitivityRepository,
    SensitivityHistoryRepository, SensitivityPresetRepository,
    UserRepository,
)
from src.domain.exceptions import NotFoundError, ValidationError
from src.infrastructure.web.middleware import role_required

patients_bp = Blueprint('patients_api', __name__, url_prefix='/api/patients')
_service = PatientService(
    PatientRepository(), PatientSensitivityRepository(),
    SensitivityHistoryRepository(), SensitivityPresetRepository(),
    UserRepository(),
)


def _calc_age(birth_date):
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _patient_to_dict(p):
    ps = PatientSensitivityRepository().find_by_patient_id(p.id)
    age = _calc_age(p.birth_date) if p.birth_date else p.age
    return dict(
        id=p.id,
        name=p.name,
        lastname=p.lastname,
        document=p.document,
        age=age,
        birth_date=p.birth_date.isoformat() if p.birth_date else None,
        diagnosis=p.diagnosis, notes=p.notes,
        user_id=p.user_id,
        created_at=p.created_at.isoformat() if p.created_at else None,
        sensitivity=ps.sensitivities if ps else None,
        user=dict(
            id=p.patient_user.id,
            email=p.patient_user.email,
            name=p.patient_user.name,
            lastname=p.patient_user.lastname,
        ) if p.patient_user else None
    )


@patients_bp.route('', methods=['GET'])
@login_required
def list_patients():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 50)
    result = _service.list_by_user_paginated(current_user.id, page, per_page, user_role=current_user.role_rel.name)
    return jsonify(
        patients=[_patient_to_dict(p) for p in result['items']],
        total=result['total'],
        page=result['page'],
        per_page=result['per_page'],
        pages=result['pages'],
    )


@patients_bp.route('', methods=['POST'])
@login_required
@role_required(1, 2)
def create_patient():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify(error='Nombre es requerido'), 400
    if not data or not data.get('lastname'):
        return jsonify(error='Apellido es requerido'), 400
    if not data or not data.get('document'):
        return jsonify(error='Documento de Indentificación es requerido'), 400
    if not data or not data.get('email'):
        return jsonify(error='Email es requerido'), 400
    if not data or not data.get('password'):
        return jsonify(error='Contraseña es requerido'), 400
    birth_date_str = data.get('birth_date')
    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date() if birth_date_str else None
    age = _calc_age(birth_date) if birth_date else data.get('age')
    # Admin can assign patient to any therapist; therapist always assigns to themselves
    owner_id = data.get('therapist_id') if current_user.role_id == 1 else None
    if owner_id is None:
        owner_id = current_user.id

    p = _service.create(
        therapist_id=owner_id,
        name=data['name'],
        lastname=data['lastname'],
        document=data['document'],
        email=data['email'],
        password=data['password'],
        birth_date=birth_date, age=age,
        diagnosis=data.get('diagnosis'), notes=data.get('notes'),
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
@role_required(1, 2)
def update_patient(pid):
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    if 'birth_date' in data and data['birth_date']:
        data['birth_date'] = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        data['age'] = _calc_age(data['birth_date'])
    try:
        p = _service.update(pid, data)
        return jsonify(_patient_to_dict(p))
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404


@patients_bp.route('/<int:pid>', methods=['DELETE'])
@login_required
@role_required(1, 2)
def delete_patient(pid):
    try:
        _service.delete(pid)
        return jsonify(ok=True)
    except NotFoundError:
        return jsonify(error='Paciente no encontrado'), 404


@patients_bp.route('/<int:pid>/transfer', methods=['PUT'])
@login_required
@role_required(1, 2)
def transfer_patient(pid):
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify(error='user_id es requerido'), 400
    try:
        p = _service.transfer(pid, data['user_id'])
        return jsonify(ok=True, message='Paciente transferido correctamente')
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
@role_required(1, 2)
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
    # Viewer can see history, admin/therapist can see it too
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
