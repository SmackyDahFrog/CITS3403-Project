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
    # secret question for password recovery — nullable so existing accounts are not broken
    secret_question = db.Column(db.String(100), nullable=True)
    secret_answer_hash = db.Column(db.String(255), nullable=True)
    def set_password(self, raw_password):
        # never store the plaintext password, only the hash
        self.password_hash = generate_password_hash(raw_password)
    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)
    def set_secret_answer(self, raw_answer):
        # normalise to lowercase so capitalisation doesn't matter on recovery
        self.secret_answer_hash = generate_password_hash(raw_answer.lower().strip())
    def check_secret_answer(self, raw_answer):
        if not self.secret_answer_hash:
            return False
        return check_password_hash(self.secret_answer_hash, raw_answer.lower().strip())
    def __repr__(self):
        return f'<User {self.username}>'
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # game key tells us which leaderboard the row belongs to, e.g. 'kai'
    game = db.Column(db.String(20), nullable=False, index=True)
    value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='scores')
    def __repr__(self):
        return f'<Score {self.game}:{self.value} user={self.user_id}>'
    
class WheresWilsonRun(db.Model):
    __tablename__ = 'wheres_wilson_runs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    time_ms = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='wheres_wilson_runs')

class TicTacToeRun(db.Model):
    __tablename__ = 'tictactoe_runs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    wins = db.Column(db.Integer, nullable=False, default=0)
    losses = db.Column(db.Integer, nullable=False, default=0)
    draws = db.Column(db.Integer, nullable=False, default=0)
    best_win_ms = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='tictactoe_runs')
    def __repr__(self):
        return f'<TicTacToeRun wins={self.wins} losses={self.losses} draws={self.draws} user={self.user_id}>'
class KaiRun(db.Model):
    __tablename__ = 'kai_runs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_ms = db.Column(db.Integer, nullable=False)
    avg_eat_ms = db.Column(db.Integer, nullable=False, default=0)
    eat_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='kai_runs')
    def __repr__(self):
        return f'<KaiRun time={self.time_ms}ms avg_eat={self.avg_eat_ms}ms user={self.user_id}>'

class Follow(db.Model):
    __tablename__ = 'follows'
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # one user only follows another once, enforced at the DB level
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='uq_follower_followed'),)
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following_links')
    followed = db.relationship('User', foreign_keys=[followed_id], backref='follower_links')
    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id}>'