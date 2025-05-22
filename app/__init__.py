import os
from flask import Flask
from config import config
from extensions import db, migrate, mail
from datetime import datetime, timezone, timedelta
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

csrf = CSRFProtect()
login_manager = LoginManager()

login_manager.login_view = 'main_bp.signin'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'

# Initialize scheduler globally, but start it within app context
scheduler = BackgroundScheduler()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure instance folder exists for SQLite databases
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        instance_folder_path = app.instance_path
        if not os.path.exists(instance_folder_path):
            try:
                os.makedirs(instance_folder_path)
            except OSError as e:
                app.logger.error(f"Error creating instance folder: {e}")

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # User loader callback for Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        if user_id is not None:
            return db.session.get(User, int(user_id))
        return None

    # Register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Inject current year into templates
    @app.context_processor
    def inject_now():
        return {'now_year': datetime.now(timezone.utc).year}

    # Start the scheduler only once when the app is created
    if not scheduler.running:
        # Import tasks here to avoid circular imports
        from .tasks import send_due_date_reminders

        # Add the job to the scheduler
        scheduler.add_job(
            func=lambda: send_due_date_reminders(app), # Pass the app instance
            trigger='cron',
            hour=0, # Run at 0 AM UTC
            minute=0,
            id='due_date_reminders',
            replace_existing=True
        )
        scheduler.start()

        # Ensure the scheduler shuts down when the app exits
        atexit.register(lambda: scheduler.shutdown())

        app.logger.info("APScheduler started and reminder job added.")

    return app