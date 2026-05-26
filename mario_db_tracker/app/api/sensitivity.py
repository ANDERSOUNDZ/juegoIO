from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import db, SensitivityPreset

sensitivity_bp = Blueprint('sensitivity_api', __name__, url_prefix='/api/sensitivity')


def preset_to_dict(p):
    return dict(
        id=p.id, name=p.name, description=p.description,
        difficulty_level=p.difficulty_level,
        sensitivities=p.sensitivities,
        is_default=p.is_default,
        created_by=p.created_by,
    )


@sensitivity_bp.route('/presets', methods=['GET'])
@login_required
def list_presets():
    presets = SensitivityPreset.query.order_by(SensitivityPreset.difficulty_level).all()
    return jsonify([preset_to_dict(p) for p in presets])


@sensitivity_bp.route('/presets', methods=['POST'])
@login_required
def create_preset():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('sensitivities'):
        return jsonify(error="name y sensitivities son requeridos"), 400

    sens = data['sensitivities']
    if not isinstance(sens, list) or len(sens) != 5:
        return jsonify(error="sensitivities debe ser una lista de 5 valores"), 400

    p = SensitivityPreset(
        name=data['name'],
        description=data.get('description'),
        difficulty_level=data.get('difficulty_level', 'custom'),
        sensitivities=sens,
        is_default=False,
        created_by=current_user.id,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(preset_to_dict(p)), 201
