import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

def str_to_bool(value):
    """Convert string environment variable to boolean."""
    return str(value).lower() in ('true', '1', 't', 'yes', 'y')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=5)  # Configure remember me cookie duration

    # Email configuration for password recovery.
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = str_to_bool(os.environ.get('MAIL_USE_TLS'))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Flask URL building outside request context
    SERVER_NAME = os.environ.get('SERVER_NAME') or 'localhost:5000'
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME') or 'http'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'instance', 'dev.db')


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'instance', 'prod.db')  # Fallback, but prod should use a proper DB


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}