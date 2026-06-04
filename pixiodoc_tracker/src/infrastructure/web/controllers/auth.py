from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager

from src.infrastructure.persistence.models import UserModel, RoleModel, db
from src.infrastructure.web.middleware import role_required

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'



def _set_role_id(user, role_name):
    """Look up role_id from roles table and set it on the user."""
    user.role = role_name
    role = RoleModel.query.filter_by(name=role_name).first()
    if role:
        user.role_id = role.id


def _validate_role(role_name):
    """Check if role exists in DB table."""
    return RoleModel.query.filter_by(name=role_name).first() is not None


@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(int(user_id))


def init_login_manager(app):
    login_manager.init_app(app)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = UserModel.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pages.dashboard'))
        flash('Email o contraseña incorrectos', 'error')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'therapist')
        if UserModel.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return render_template('register.html')
        user = UserModel(email=email, name=name)
        _set_role_id(user, role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('pages.dashboard'))
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    user = UserModel.query.filter_by(email=data.get('email', '')).first()
    if user and user.check_password(data.get('password', '')):
        login_user(user)
        return jsonify(id=user.id, name=user.name, email=user.email, role=user.role)
    return jsonify(error='Credenciales inválidas'), 401


@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')
    if not all([email, name, password]):
        return jsonify(error='email, name y password son requeridos'), 400
    if UserModel.query.filter_by(email=email).first():
        return jsonify(error='El email ya está registrado'), 409
    user = UserModel(email=email, name=name)
    _set_role_id(user, data.get('role', 'therapist'))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role), 201


@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify(ok=True)


# ─── Therapists list ──────────────────────────────────────────────


@auth_bp.route('/api/users/therapists', methods=['GET'])
@login_required
@role_required('admin', 'therapist')
def api_list_therapists():
    therapists = UserModel.query.filter(
        UserModel.role.in_(['therapist', 'admin'])
    ).order_by(UserModel.name).all()
    return jsonify([
        dict(id=u.id, name=u.name, email=u.email, role=u.role)
        for u in therapists
    ])


# ─── Admin: User Management ────────────────────────────────────────


@auth_bp.route('/api/users', methods=['GET'])
@login_required
@role_required('admin')
def api_list_users():
    users = UserModel.query.order_by(UserModel.name).all()
    return jsonify([
        dict(id=u.id, name=u.name, email=u.email, role=u.role, created_at=u.created_at.isoformat() if u.created_at else None)
        for u in users
    ])


@auth_bp.route('/api/users', methods=['POST'])
@login_required
@role_required('admin')
def api_create_user():
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'therapist')
    if not all([email, name, password]):
        return jsonify(error='email, name y password son requeridos'), 400
    if not _validate_role(role):
        return jsonify(error='Rol inválido'), 400
    if UserModel.query.filter_by(email=email).first():
        return jsonify(error='El email ya está registrado'), 409
    user = UserModel(email=email, name=name)
    _set_role_id(user, role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role), 201


@auth_bp.route('/api/users/<int:uid>', methods=['PUT'])
@login_required
@role_required('admin')
def api_update_user(uid):
    data = request.get_json()
    if not data:
        return jsonify(error='JSON requerido'), 400
    user = UserModel.query.get(uid)
    if not user:
        return jsonify(error='Usuario no encontrado'), 404
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if data['email'] != user.email and UserModel.query.filter_by(email=data['email']).first():
            return jsonify(error='El email ya está registrado'), 409
        user.email = data['email']
    if 'role' in data:
        if not _validate_role(data['role']):
            return jsonify(error='Rol inválido'), 400
        _set_role_id(user, data['role'])
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role)


@auth_bp.route('/api/users/<int:uid>', methods=['DELETE'])
@login_required
@role_required('admin')
def api_delete_user(uid):
    user = UserModel.query.get(uid)
    if not user:
        return jsonify(error='Usuario no encontrado'), 404
    if user.id == current_user.id:
        return jsonify(error='No puedes eliminarte a ti mismo'), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify(ok=True)
