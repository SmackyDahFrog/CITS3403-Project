from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from app.config import Config
from app.models import db, User

load_dotenv()

login_manager = LoginManager()
migrate = Migrate()
# global csrf check, covers JSON endpoints like /api/scores that don't go through a FlaskForm
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    #bind extensions to the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    csrf.init_app(app)

    #  blueprint holds every route under main.*
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # build any missing tables on first boot so dev runs without flask db upgrade
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    # flask-login passes the id back as a string
    return User.query.get(int(user_id))
