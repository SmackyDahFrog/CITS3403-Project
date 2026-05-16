from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, ValidationError
from app.models import User

SECRET_QUESTIONS = [
    ('', '— Select a question —'),
    ("What was the name of your first pet?", "What was the name of your first pet?"),
    ("What was the name of your first school?", "What was the name of your first school?"),
    ("What city were you born in?", "What city were you born in?"),
    ("What is your favourite childhood book?", "What is your favourite childhood book?"),
    ("What is your mother's maiden name?", "What is your mother's maiden name?"),
]

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=4, max=15)],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, max=32),
            Regexp(r'.*\d.*', message='Password must contain at least one number.'),
        ],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords do not match.')],
    )
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('That username is already taken.')

class CustomisationForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=20)])
    avatar = StringField('Avatar', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Save')

class ChangeDisplayNameForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=20)])
    submit_displayname = SubmitField('Save display name')

class ChangeAvatarForm(FlaskForm):
    avatar = StringField('Avatar', validators=[DataRequired(), Length(max=20)])
    submit_avatar = SubmitField('Save avatar')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, max=32),
            Regexp(r'.*\d.*', message='Password must contain at least one number.'),
        ],
    )
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords do not match.')],
    )
    submit_password = SubmitField('Change password')

class SetSecretQuestionForm(FlaskForm):
    secret_question = SelectField('Secret Question', choices=SECRET_QUESTIONS, validators=[DataRequired()])
    secret_answer = StringField('Answer', validators=[DataRequired(), Length(min=2, max=100)])
    submit_secret = SubmitField('Save secret question')

class ForgotPasswordStep1Form(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=15)])
    submit = SubmitField('Continue')

class ForgotPasswordAnswerForm(FlaskForm):
    answer = StringField('Answer', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Verify')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, max=32),
            Regexp(r'.*\d.*', message='Password must contain at least one number.'),
        ],
    )
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords do not match.')],
    )
    submit = SubmitField('Reset Password')