from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, ValidationError

from app.models import User


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
            #at least one digit, matches the client-side rule in signup.js
            Regexp(r'.*\d.*', message='Password must contain at least one number.'),
        ],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords do not match.')],
    )
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        #  unique check against the users table
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('That username is already taken.')


class CustomisationForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired(), Length(max=20)])
    avatar = StringField('Avatar', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Save')
