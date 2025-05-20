# app/__init__.py
import os
from flask import Flask
from config import config
from extensions import db, migrate
from datetime import datetime, timezone
from flask_wtf import CSRFProtect
from flask_login import LoginManager # Importe LoginManager

# Inicialize CSRFProtect e LoginManager sem o app context
csrf = CSRFProtect()
login_manager = LoginManager()

# Configurações do Flask-Login
login_manager.login_view = 'main_bp.signin' # Define a rota para onde redirecionar usuários não logados
login_manager.login_message_category = 'info' # Categoria da mensagem flash padrão
login_manager.login_message = 'Please log in to access this page.' # Mensagem padrão

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        instance_folder_path = os.path.join(app.instance_path)
        if not os.path.exists(instance_folder_path):
            try:
                os.makedirs(instance_folder_path)
            except OSError as e:
                app.logger.error(f"Error creating instance folder: {e}")

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app) # Inicialize LoginManager com o app context

    # User loader para Flask-Login
    # Esta função é usada pelo Flask-Login para carregar um usuário
    # a partir do ID armazenado na sessão.
    from .models import User # Importe o modelo User aqui para evitar importação circular
    @login_manager.user_loader
    def load_user(user_id):
        # user_id é uma string, converta para o tipo correto do seu ID de usuário (geralmente int)
        if user_id is not None:
            return db.session.get(User, int(user_id)) # Use db.session.get para buscar por PK
        return None

    # Register Blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Context processors
    @app.context_processor
    def inject_now():
        return {'now_year': datetime.now(timezone.utc).year}

    return app