from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import CustomisationForm, LoginForm, SignupForm
from app.models import Score, User, db

main_bp = Blueprint('main', __name__)

# only games we are willing to record scores for, blocks the api from being a generic write target
ALLOWED_GAMES = {'kai', 'tictactoe', 'wilson'}


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
    # top 3 kai scores for the panel below the canvas, joined with users for display name fallback
    top_scores = (
        db.session.query(Score, User)
            .join(User, Score.user_id == User.id)
            .filter(Score.game == 'kai')
            .order_by(Score.value.desc())
            .limit(3)
            .all()
    )
    return render_template('games/kai.html', top_scores=top_scores)


@main_bp.route('/api/scores', methods=['POST'])
@login_required
def api_save_score():
    # tiny json endpoint, the kai client posts here on game over
    data = request.get_json(silent=True) or {}
    game = data.get('game')
    value = data.get('value')

    # bool is an int subclass in python, exclude it explicitly so True/False can't sneak through
    if game not in ALLOWED_GAMES or isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return jsonify(ok=False, error='invalid payload'), 400

    db.session.add(Score(user_id=current_user.id, game=game, value=value))
    db.session.commit()
    return jsonify(ok=True)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
