from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import db, Patient, PatientSensitivity, SensitivityHistory, SensitivityPreset
from datetime import datetime, timezone

patients_bp = Blueprint('patients_api', __name__, url_prefix='/api/patients')


def patient_to_dict(p):
    return dict(
        id=p.id, name=p.name, age=p.age,
        diagnosis=p.diagnosis, notes=p.notes,
        user_id=p.user_id,
        created_at=p.created_at.isoformat() if p.created_at else None,
        sensitivity=p.sensitivity.sensitivities if p.sensitivity else None,
    )


@patients_bp.route('', methods=['GET'])
@login_required
def list_patients():
    patients = Patient.query.filter_by(user_id=current_user.id).order_by(Patient.name).all()
    return jsonify([patient_to_dict(p) for p in patients])


@patients_bp.route('', methods=['POST'])
@login_required
def create_patient():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify(error="name es requerido"), 400

    p = Patient(
        user_id=current_user.id,
        name=data['name'],
        age=data.get('age'),
        diagnosis=data.get('diagnosis'),
        notes=data.get('notes'),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(patient_to_dict(p)), 201


@patients_bp.route('/<int:pid>', methods=['GET'])
@login_required
def get_patient(pid):
    p = Patient.query.get_or_404(pid)
    return jsonify(patient_to_dict(p))


@patients_bp.route('/<int:pid>', methods=['PUT'])
@login_required
def update_patient(pid):
    p = Patient.query.get_or_404(pid)
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    for field in ('name', 'age', 'diagnosis', 'notes'):
        if field in data:
            setattr(p, field, data[field])

    db.session.commit()
    return jsonify(patient_to_dict(p))


@patients_bp.route('/<int:pid>', methods=['DELETE'])
@login_required
def delete_patient(pid):
    p = Patient.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify(ok=True)


# ─── Sensibilidad por paciente ──────────────────────────────────

@patients_bp.route('/<int:pid>/sensitivity', methods=['GET'])
@login_required
def get_sensitivity(pid):
    Patient.query.get_or_404(pid)
    ps = PatientSensitivity.query.filter_by(patient_id=pid).first()
    if not ps:
        return jsonify(sensitivities=None, preset=None)

    preset_info = None
    if ps.preset:
        preset_info = dict(id=ps.preset.id, name=ps.preset.name, difficulty_level=ps.preset.difficulty_level)

    return jsonify(
        sensitivities=ps.sensitivities,
        preset=preset_info,
        updated_at=ps.updated_at.isoformat() if ps.updated_at else None,
    )


@patients_bp.route('/<int:pid>/sensitivity', methods=['PUT'])
@login_required
def update_sensitivity(pid):
    Patient.query.get_or_404(pid)
    data = request.get_json()
    if not data or 'sensitivities' not in data:
        return jsonify(error="sensitivities es requerido"), 400

    new_sens = data['sensitivities']
    if not isinstance(new_sens, list) or len(new_sens) != 5:
        return jsonify(error="sensitivities debe ser una lista de 5 valores"), 400

    ps = PatientSensitivity.query.filter_by(patient_id=pid).first()
    old_sens = ps.sensitivities if ps else None

    # Save history
    history = SensitivityHistory(
        patient_id=pid,
        old_sensitivities=old_sens,
        new_sensitivities=new_sens,
        reason=data.get('reason'),
        changed_by=current_user.id,
    )
    db.session.add(history)

    # Update or create
    if ps:
        ps.sensitivities = new_sens
        ps.based_on_preset = data.get('preset_id')
        ps.updated_at = datetime.now(timezone.utc)
        ps.updated_by = current_user.id
    else:
        ps = PatientSensitivity(
            patient_id=pid,
            sensitivities=new_sens,
            based_on_preset=data.get('preset_id'),
            updated_by=current_user.id,
        )
        db.session.add(ps)

    db.session.commit()
    return jsonify(sensitivities=ps.sensitivities, ok=True)


@patients_bp.route('/<int:pid>/sensitivity/history', methods=['GET'])
@login_required
def sensitivity_history(pid):
    Patient.query.get_or_404(pid)
    history = SensitivityHistory.query.filter_by(patient_id=pid).order_by(SensitivityHistory.changed_at.desc()).all()
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
