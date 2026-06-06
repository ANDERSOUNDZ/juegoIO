from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from src.infrastructure.web.middleware import role_required
from src.application.game_service import GameService
from src.infrastructure.persistence.repositories import GameRepository, PlayerGameConfigRepository
from games.registry import get_game_info

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
@role_required(1, 2, 3)
def games_page():
    return render_template('games.html')


@main_bp.route('/play/<int:game_id>')
@login_required
@role_required(1, 2, 3)
def play_game(game_id):
    try:
        game = _game_service.get_by_id(game_id)
        if game and game.config:
            gtype = game.config.get('metadata', {}).get('type', 'platformer')
            info = get_game_info(gtype)
            # Los juegos Phaser usan play.html (ref-hand, calibración, acciones
            # filtradas); los de emulador usan emulator/template.html (Nostalgist).
            if info.get('type') == 'phaser':
                return render_template('play.html', game_id=game_id)
            return render_template(info['dir'] + '/template.html', game_id=game_id)
    except Exception:
        pass
    return render_template('play.html', game_id=game_id)


@main_bp.route('/sessions/<int:sid>/report')
@login_required
def session_report(sid):
    return render_template('report.html', session_id=sid)


@main_bp.route('/admin/users')
@login_required
@role_required(1)
def admin_users():
    return render_template('admin_users.html')

@main_bp.route('/profile/<int:user_id>')
@login_required
def profile_page(user_id):
    return render_template('profile.html', user_id=user_id)
