import os
from flask import Flask
from config import config
from extensions import db, migrate
from datetime import datetime, timezone

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
        # Note: The actual DB file path is now fully defined in config.py

    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprints
    from .routes import main_bp 
    app.register_blueprint(main_bp)

    # Context processors
    @app.context_processor
    def inject_now():
        return {'now_year': datetime.now(timezone.utc).year}

    return app