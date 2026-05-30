from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from src.application.sensitivity_service import SensitivityService
from src.infrastructure.persistence.repositories import SensitivityPresetRepository
from src.domain.exceptions import ValidationError

sensitivity_bp = Blueprint('sensitivity_api', __name__, url_prefix='/api/sensitivity')
_service = SensitivityService(SensitivityPresetRepository())


def _preset_to_dict(p):
    return dict(
        id=p.id, name=p.name, description=p.description,
        difficulty_level=p.difficulty_level,
        sensitivities=p.sensitivities,
        is_default=p.is_default, created_by=p.created_by,
    )


@sensitivity_bp.route('/presets', methods=['GET'])
@login_required
def list_presets():
    presets = _service.list_presets()
    return jsonify([_preset_to_dict(p) for p in presets])


@sensitivity_bp.route('/presets', methods=['POST'])
@login_required
def create_preset():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    try:
        p = _service.create_preset(
            name=data.get('name', ''),
            sensitivities=data.get('sensitivities', []),
            description=data.get('description'),
            difficulty_level=data.get('difficulty_level', 'custom'),
            created_by=current_user.id,
        )
        return jsonify(_preset_to_dict(p)), 201
    except ValidationError as e:
        return jsonify(error=str(e)), 400
