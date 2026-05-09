import os
import time
from collections import defaultdict, deque
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import CustomisationForm, LoginForm, SignupForm
from app.models import KaiRun, Score, User, db

main_bp = Blueprint('main', __name__)

# per-IP timestamps for the username probe, keeps abusers from hammering it
_username_check_hits = defaultdict(deque)
USERNAME_CHECK_WINDOW = 10.0
USERNAME_CHECK_LIMIT = 20

# games still on the legacy generic scores table. kai now writes to its own kai_runs table
# via /api/kai/runs, so it's intentionally absent from this allow-list
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
    # lightweight uniqueness probe used by signup.js to flag taken names live
    ip = request.remote_addr or 'unknown'
    now = time.time()
    hits = _username_check_hits[ip]
    # drop entries that have aged out of the window
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
    # only basic chars are accepted, mirrors what we'd want stored
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

@main_bp.route('/tictactoe')
@login_required
def tictactoe():
    return render_template('ticTacToe.html')

@main_bp.route('/game1')
@login_required
def game1():
    return render_template('game1.html')

@main_bp.route('/play/kai')
@login_required
def play_kai():
    # one row per user, ordered by survival time then by avg-eat-ms ascending as a tiebreak.
    # avg_eat_ms = 0 means there were no inter-eat gaps long enough to count, so push those
    # rows to the bottom of any tie rather than letting a "no data" zero rank above real avgs
    avg_eat_no_data = db.case((KaiRun.avg_eat_ms == 0, 1), else_=0)
    top_scores = (
        db.session.query(KaiRun, User)
            .join(User, KaiRun.user_id == User.id)
            .order_by(KaiRun.time_ms.desc(), avg_eat_no_data.asc(), KaiRun.avg_eat_ms.asc())
            .limit(3)
            .all()
    )
    # the current user's own best, shown in a separate "Your Best" panel even when they
    # aren't in the top 3, so a subpar run still updates a visible record after reload
    personal_run = db.session.query(KaiRun).filter_by(user_id=current_user.id).first()
    # cache-buster so iterating on kai-game.js during dev doesn't get clobbered by stale browser caches
    js_path = os.path.join(current_app.static_folder, 'js', 'kai-game.js')
    js_version = int(os.path.getmtime(js_path))
    return render_template(
        'games/kai.html',
        top_scores=top_scores,
        personal_run=personal_run,
        js_version=js_version,
    )


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


def _kai_run_is_better(new_time, new_avg, old_time, old_avg):
    # primary: a longer survival time always wins outright
    if new_time != old_time:
        return new_time > old_time
    # tie on time, fall back to per-eat pacing: lower avg ms is better, treat 0 ("no
    # qualifying eat gaps recorded") as worst so a real measured average always beats it
    new_cmp = new_avg if new_avg > 0 else float('inf')
    old_cmp = old_avg if old_avg > 0 else float('inf')
    return new_cmp < old_cmp


@main_bp.route('/api/kai/runs', methods=['POST'])
@login_required
def api_save_kai_run():
    # kai-specific endpoint, each user keeps a single best-run row in kai_runs that gets
    # overwritten only when the new run beats it on time, or ties on time with a better
    # (lower) inter-eat average. weaker runs are silently dropped, the request still 200s
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
        # created_at tracks when the current best was set, refresh it on every overwrite
        existing.created_at = datetime.utcnow()
        db.session.commit()
        is_new_best = True
    # client uses is_new_best to decide whether to reload the page so the leaderboard and
    # the Your Best panel reflect the freshly-saved row
    return jsonify(ok=True, is_new_best=is_new_best)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
