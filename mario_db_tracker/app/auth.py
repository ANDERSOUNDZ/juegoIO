from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))

        flash('Email o contraseña incorrectos', 'error')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'therapist')

        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return render_template('register.html')

        user = User(email=email, name=name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# ─── API endpoints for auth ────────────────────────────────────

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    user = User.query.filter_by(email=data.get('email', '')).first()
    if user and user.check_password(data.get('password', '')):
        login_user(user)
        return jsonify(id=user.id, name=user.name, email=user.email, role=user.role)

    return jsonify(error="Credenciales inválidas"), 401


@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify(error="JSON requerido"), 400

    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')

    if not all([email, name, password]):
        return jsonify(error="email, name y password son requeridos"), 400

    if User.query.filter_by(email=email).first():
        return jsonify(error="El email ya está registrado"), 409

    user = User(email=email, name=name, role=data.get('role', 'therapist'))
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
