import os
import time
from collections import defaultdict, deque
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import (
    ChangeAvatarForm,
    ChangeDisplayNameForm,
    ChangePasswordForm,
    CustomisationForm,
    ForgotPasswordAnswerForm,
    ForgotPasswordStep1Form,
    LoginForm,
    ResetPasswordForm,
    SetSecretQuestionForm,
    SignupForm,
)
from app.models import WheresWilsonRun, KaiRun, Score, TicTacToeRun, User, db

main_bp = Blueprint('main', __name__)

# per-IP timestamps for the username probe
_username_check_hits = defaultdict(deque)
USERNAME_CHECK_WINDOW = 10.0
USERNAME_CHECK_LIMIT = 20

ALLOWED_GAMES = {'tictactoe', 'wilson'}


@main_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.stages'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.stages'))
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('main.login'))
    return render_template('MainPage.html', form=form)


@main_bp.route('/check-username')
def check_username():
    ip = request.remote_addr or 'unknown'
    now = time.time()
    hits = _username_check_hits[ip]
    while hits and now - hits[0] > USERNAME_CHECK_WINDOW:
        hits.popleft()
    if len(hits) >= USERNAME_CHECK_LIMIT:
        return jsonify({'available': False, 'reason': 'rate_limited'}), 429
    hits.append(now)

    username = request.args.get('username', '').strip()
    if len(username) < 4:
        return jsonify({'available': False, 'reason': 'short'})
    if len(username) > 15:
        return jsonify({'available': False, 'reason': 'long'})
    if not all(c.isalnum() or c in ('_', '-') for c in username):
        return jsonify({'available': False, 'reason': 'invalid'})
    taken = User.query.filter_by(username=username).first() is not None
    return jsonify({'available': not taken, 'reason': 'taken' if taken else None})


@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
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
        if form.secret_question.data:
            current_user.secret_question = form.secret_question.data
            current_user.set_secret_answer(form.secret_answer.data)
        db.session.commit()
        return redirect(url_for('main.stages'))
    return render_template('customisation.html', form=form)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form_displayname = ChangeDisplayNameForm()
    form_avatar = ChangeAvatarForm()
    form_password = ChangePasswordForm()
    form_secret = SetSecretQuestionForm()

    if form_displayname.submit_displayname.data and form_displayname.validate():
        current_user.display_name = form_displayname.display_name.data
        db.session.commit()
        flash('Display name updated.', 'success')
        return redirect(url_for('main.settings'))

    if form_avatar.submit_avatar.data and form_avatar.validate():
        current_user.avatar = form_avatar.avatar.data
        db.session.commit()
        flash('Avatar updated.', 'success')
        return redirect(url_for('main.settings'))

    if form_password.submit_password.data and form_password.validate():
        if not current_user.check_password(form_password.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form_password.new_password.data)
            db.session.commit()
            flash('Password changed.', 'success')
            return redirect(url_for('main.settings'))

    if form_secret.submit_secret.data and form_secret.validate():
        current_user.secret_question = form_secret.secret_question.data
        current_user.set_secret_answer(form_secret.secret_answer.data)
        db.session.commit()
        flash('Secret question saved.', 'success')
        return redirect(url_for('main.settings'))

    # prepopulate fields on GET
    if not form_displayname.display_name.data:
        form_displayname.display_name.data = current_user.display_name or ''
    if not form_avatar.avatar.data:
        form_avatar.avatar.data = current_user.avatar or 'av1'
    if not form_secret.secret_question.data:
        form_secret.secret_question.data = current_user.secret_question or ''

    return render_template(
        'settings.html',
        form_displayname=form_displayname,
        form_avatar=form_avatar,
        form_password=form_password,
        form_secret=form_secret,
    )


@main_bp.route('/stages')
@login_required
def stages():
    return render_template('stages.html')


@main_bp.route('/tictactoe')
@login_required
def tictactoe():
    top_scores = (
        db.session.query(TicTacToeRun, User)
            .join(User, TicTacToeRun.user_id == User.id)
            .filter(TicTacToeRun.best_win_ms.isnot(None))
            .order_by(TicTacToeRun.best_win_ms.asc())
            .limit(3)
            .all()
    )
    personal_run = db.session.query(TicTacToeRun).filter_by(user_id=current_user.id).first()
    return render_template('ticTacToe.html', top_scores=top_scores, personal_run=personal_run)


@main_bp.route('/game1')
@login_required
def game1():
    top_scores = (
        db.session.query(WheresWilsonRun, User)
        .join(User, WheresWilsonRun.user_id == User.id)
        .order_by(WheresWilsonRun.time_ms.asc())
        .limit(3)
        .all()
    )

    personal_run = db.session.query(WheresWilsonRun).filter_by(user_id=current_user.id).first()
    return render_template('game1.html', top_scores=top_scores, personal_run=personal_run)


@main_bp.route('/play/kai')
@login_required
def play_kai():
    avg_eat_no_data = db.case((KaiRun.avg_eat_ms == 0, 1), else_=0)
    top_scores = (
        db.session.query(KaiRun, User)
            .join(User, KaiRun.user_id == User.id)
            .order_by(KaiRun.time_ms.desc(), avg_eat_no_data.asc(), KaiRun.avg_eat_ms.asc())
            .limit(3)
            .all()
    )
    personal_run = db.session.query(KaiRun).filter_by(user_id=current_user.id).first()
    js_path = os.path.join(current_app.static_folder, 'js', 'kai-game.js')
    js_version = int(os.path.getmtime(js_path))
    return render_template(
        'games/kai.html',
        top_scores=top_scores,
        personal_run=personal_run,
        js_version=js_version,
    )


@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.stages'))
    form = ForgotPasswordStep1Form()
    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()
        if user and user.secret_question:
            return redirect(url_for('main.forgot_password_question', username=username))
        flash('No recovery question found for that username.', 'danger')
        return redirect(url_for('main.forgot_password'))
    return render_template('forgot_password.html', form=form)


@main_bp.route('/forgot-password/<username>', methods=['GET', 'POST'])
def forgot_password_question(username):
    if current_user.is_authenticated:
        return redirect(url_for('main.stages'))
    user = User.query.filter_by(username=username).first()
    if not user or not user.secret_question:
        return redirect(url_for('main.forgot_password'))
    form = ForgotPasswordAnswerForm()
    if form.validate_on_submit():
        if user.check_secret_answer(form.answer.data):
            session['reset_allowed_for'] = username
            return redirect(url_for('main.reset_password', username=username))
        flash('Incorrect answer. Please try again.', 'danger')
        return redirect(url_for('main.forgot_password_question', username=username))
    return render_template('forgot_password_question.html', form=form, question=user.secret_question)


@main_bp.route('/reset-password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if current_user.is_authenticated:
        return redirect(url_for('main.stages'))
    # only allow access if the user correctly answered their secret question
    if session.get('reset_allowed_for') != username:
        return redirect(url_for('main.forgot_password'))
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('main.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        session.pop('reset_allowed_for', None)
        flash('Password reset successfully. You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_password.html', form=form, username=username)


@main_bp.route('/api/scores', methods=['POST'])
@login_required
def api_save_score():
    data = request.get_json(silent=True) or {}
    game = data.get('game')
    value = data.get('value')
    if game not in ALLOWED_GAMES or isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return jsonify(ok=False, error='invalid payload'), 400
    db.session.add(Score(user_id=current_user.id, game=game, value=value))
    db.session.commit()
    return jsonify(ok=True)


def _is_nonneg_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _kai_run_is_better(new_time, new_avg, old_time, old_avg):
    if new_time != old_time:
        return new_time > old_time
    new_cmp = new_avg if new_avg > 0 else float('inf')
    old_cmp = old_avg if old_avg > 0 else float('inf')
    return new_cmp < old_cmp


@main_bp.route('/api/kai/runs', methods=['POST'])
@login_required
def api_save_kai_run():
    data = request.get_json(silent=True) or {}
    time_ms = data.get('time_ms')
    avg_eat_ms = data.get('avg_eat_ms', 0)
    eat_count = data.get('eat_count', 0)
    if not (_is_nonneg_int(time_ms) and _is_nonneg_int(avg_eat_ms) and _is_nonneg_int(eat_count)):
        return jsonify(ok=False, error='invalid payload'), 400
    existing = db.session.query(KaiRun).filter_by(user_id=current_user.id).first()
    is_new_best = False
    if existing is None:
        db.session.add(KaiRun(
            user_id=current_user.id,
            time_ms=time_ms,
            avg_eat_ms=avg_eat_ms,
            eat_count=eat_count,
        ))
        db.session.commit()
        is_new_best = True
    elif _kai_run_is_better(time_ms, avg_eat_ms, existing.time_ms, existing.avg_eat_ms):
        existing.time_ms = time_ms
        existing.avg_eat_ms = avg_eat_ms
        existing.eat_count = eat_count
        existing.created_at = datetime.utcnow()
        db.session.commit()
        is_new_best = True
    return jsonify(ok=True, is_new_best=is_new_best)


@main_bp.route('/api/tictactoe/runs', methods=['POST'])
@login_required
def api_save_tictactoe_run():
    data = request.get_json(silent=True) or {}
    result = data.get('result')
    time_ms = data.get('time_ms')
    if result not in ('win', 'loss', 'draw'):
        return jsonify(ok=False, error='invalid payload'), 400
    if result == 'win' and not _is_nonneg_int(time_ms):
        return jsonify(ok=False, error='invalid payload'), 400
    existing = db.session.query(TicTacToeRun).filter_by(user_id=current_user.id).first()
    if existing is None:
        existing = TicTacToeRun(user_id=current_user.id, wins=0, losses=0, draws=0)
        db.session.add(existing)
    if result == 'win':
        existing.wins += 1
        if existing.best_win_ms is None or time_ms < existing.best_win_ms:
            existing.best_win_ms = time_ms
    elif result == 'loss':
        existing.losses += 1
    else:
        existing.draws += 1
    existing.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(ok=True)

@main_bp.route('/api/game1/runs', methods=['POST'])
@login_required
def api_save_whereswilson_run():
    data = request.get_json(silent=True) or {}
    time_ms = data.get('time_ms')

    if not _is_nonneg_int(time_ms):
        return jsonify(ok=False, error='invalid payload'), 400
    
    existing = db.session.query(WheresWilsonRun).filter_by(user_id=current_user.id).first()
    is_new_best = False

    if existing is None:
        existing = WheresWilsonRun(user_id=current_user.id, time_ms=time_ms)
        db.session.add(existing)
        is_new_best = True
    elif time_ms < existing.time_ms:
        existing.time_ms = time_ms
        existing.created_at = datetime.utcnow()
        is_new_best = True
    
    db.session.commit()
    return jsonify(ok=True, is_new_best=is_new_best)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))