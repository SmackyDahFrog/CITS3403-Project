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
    # per-game table, one row per Snack-Time playthrough. other games will get their own
    # table each, the legacy scores table sticks around for the games that haven't migrated yet
    __tablename__ = 'kai_runs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # total survival time in milliseconds, the leaderboard metric
    time_ms = db.Column(db.Integer, nullable=False)
    # average milliseconds between eats. eats happening within 100 ms of the previous one
    # don't contribute, so chain-eats on a freshly spawned ball can't drag the average down
    avg_eat_ms = db.Column(db.Integer, nullable=False, default=0)
    # raw eat count, kept for context even though the average filters some of these out
    eat_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='kai_runs')

    def __repr__(self):
        return f'<KaiRun time={self.time_ms}ms avg_eat={self.avg_eat_ms}ms user={self.user_id}>'
