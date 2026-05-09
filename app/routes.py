import os

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import CustomisationForm, LoginForm, SignupForm
from app.models import KaiRun, Score, User, db

main_bp = Blueprint('main', __name__)

# games still on the legacy generic scores table. kai now writes to its own kai_runs table
# via /api/kai/runs, so it's intentionally absent from this allow-list
ALLOWED_GAMES = {'tictactoe', 'wilson'}


@main_bp.route('/', methods=['GET', 'POST'])
def login():
    # already authenticated users skip the login screen
    if current_user.is_authenticated:
        return redirect(url_for('main.stages'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.stages'))
        flash('Invalid username or password.', 'danger')

    return render_template('MainPage.html', form=form)


@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        #log them straight in so customisation can know who they are
        login_user(user)
        return redirect(url_for('main.customisation'))

    return render_template('signup.html', form=form)


@main_bp.route('/customisation', methods=['GET', 'POST'])
@login_required
def customisation():
    form = CustomisationForm()
    if form.validate_on_submit():
        current_user.display_name = form.display_name.data
        current_user.avatar = form.avatar.data
        db.session.commit()
        return redirect(url_for('main.stages'))

    return render_template('customisation.html', form=form)


@main_bp.route('/stages')
@login_required
def stages():
    return render_template('stages.html')


@main_bp.route('/play/kai')
@login_required
def play_kai():
    # top 3 kai runs for the panel below the canvas, joined with users for display name fallback
    top_scores = (
        db.session.query(KaiRun, User)
            .join(User, KaiRun.user_id == User.id)
            .order_by(KaiRun.time_ms.desc())
            .limit(3)
            .all()
    )
    # current player's personal best, in ms, drives the live hunger-bar colour client side
    personal_best = (
        db.session.query(db.func.max(KaiRun.time_ms))
            .filter(KaiRun.user_id == current_user.id)
            .scalar()
    ) or 0
    # cache-buster so iterating on kai-game.js during dev doesn't get clobbered by stale browser caches
    js_path = os.path.join(current_app.static_folder, 'js', 'kai-game.js')
    js_version = int(os.path.getmtime(js_path))
    return render_template('games/kai.html', top_scores=top_scores, personal_best=personal_best, js_version=js_version)


@main_bp.route('/api/scores', methods=['POST'])
@login_required
def api_save_score():
    # tiny json endpoint for the legacy shared scores table, used by tictactoe and wilson
    data = request.get_json(silent=True) or {}
    game = data.get('game')
    value = data.get('value')

    # bool is an int subclass in python, exclude it explicitly so True/False can't sneak through
    if game not in ALLOWED_GAMES or isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return jsonify(ok=False, error='invalid payload'), 400

    db.session.add(Score(user_id=current_user.id, game=game, value=value))
    db.session.commit()
    return jsonify(ok=True)


def _is_nonneg_int(v):
    # bool is an int subclass in python, exclude it explicitly so True/False can't sneak in
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


@main_bp.route('/api/kai/runs', methods=['POST'])
@login_required
def api_save_kai_run():
    # kai-specific endpoint, takes the structured run payload that the legacy /api/scores
    # couldn't carry. one row per game over, written into kai_runs
    data = request.get_json(silent=True) or {}
    time_ms = data.get('time_ms')
    avg_eat_ms = data.get('avg_eat_ms', 0)
    eat_count = data.get('eat_count', 0)

    if not (_is_nonneg_int(time_ms) and _is_nonneg_int(avg_eat_ms) and _is_nonneg_int(eat_count)):
        return jsonify(ok=False, error='invalid payload'), 400

    db.session.add(KaiRun(
        user_id=current_user.id,
        time_ms=time_ms,
        avg_eat_ms=avg_eat_ms,
        eat_count=eat_count,
    ))
    db.session.commit()
    return jsonify(ok=True)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
