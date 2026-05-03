import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    #pulled from .env at runtime, fallback for local dev only
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-me'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    SESSION_PERMANENT = False


class DevelopmentConfig(Config):
    # sqlite file lives next to app/ so it stays out of static
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'user.db')
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    #wtforms csrf gets in the way of unit tests
    WTF_CSRF_ENABLED = False
