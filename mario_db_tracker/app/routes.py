from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/patients')
@login_required
def patients_page():
    return render_template('patients.html')


@main_bp.route('/patients/<int:pid>')
@login_required
def patient_detail(pid):
    return render_template('patient_detail.html', patient_id=pid)


@main_bp.route('/games')
@login_required
def games_page():
    return render_template('games.html')


@main_bp.route('/play/<int:game_id>')
@login_required
def play_game(game_id):
    return render_template('play.html', game_id=game_id)


@main_bp.route('/sessions/<int:sid>/report')
@login_required
def session_report(sid):
    return render_template('report.html', session_id=sid)


@main_bp.route('/legacy')
def legacy():
    return render_template('index.html')
