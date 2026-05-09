from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import CustomisationForm, LoginForm, SignupForm
from app.models import User, db

main_bp = Blueprint('main', __name__)


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
