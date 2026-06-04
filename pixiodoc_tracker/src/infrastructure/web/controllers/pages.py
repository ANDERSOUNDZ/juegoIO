from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from src.infrastructure.web.middleware import role_required
from src.application.game_service import GameService
from src.infrastructure.persistence.repositories import GameRepository, PlayerGameConfigRepository

main_bp = Blueprint('pages', __name__)
_game_service = GameService(GameRepository(), PlayerGameConfigRepository())


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
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
@role_required('admin', 'therapist')
def games_page():
    return render_template('games.html')


@main_bp.route('/play/<int:game_id>')
@login_required
@role_required('admin', 'therapist')
def play_game(game_id):
    try:
        game = _game_service.get_by_id(game_id)
        if game and game.config and game.config.get('metadata', {}).get('type') == 'prince':
            return render_template('play_prince.html', game_id=game_id)
    except Exception:
        pass
    return render_template('play.html', game_id=game_id)


@main_bp.route('/sessions/<int:sid>/report')
@login_required
def session_report(sid):
    return render_template('report.html', session_id=sid)


@main_bp.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    return render_template('admin_users.html')
