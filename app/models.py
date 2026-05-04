from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    #  set on the customisation page after signup
    display_name = db.Column(db.String(20), nullable=True)
    avatar = db.Column(db.String(20), nullable=True, default='av1')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        # never store the plaintext password, only the hash
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f'<User {self.username}>'
