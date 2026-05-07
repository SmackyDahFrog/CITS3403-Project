import time
from collections import defaultdict, deque

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import CustomisationForm, LoginForm, SignupForm
from app.models import User, db

main_bp = Blueprint('main', __name__)

# per-IP timestamps for the username probe, keeps abusers from hammering it
_username_check_hits = defaultdict(deque)
USERNAME_CHECK_WINDOW = 10.0
USERNAME_CHECK_LIMIT = 20


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

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
