import os
from flask import Flask
from config import config
from extensions import db, migrate
from datetime import datetime, timezone
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler 
import atexit 

csrf = CSRFProtect()
login_manager = LoginManager()
mail = Mail()

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
    login_manager.init_app(app)
    mail.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        if user_id is not None:
            return db.session.get(User, int(user_id))
        return None

    from .routes import main_bp
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_now():
        return {'now_year': datetime.now(timezone.utc).year}
    
    # Start the scheduler only once when the app is created
    if not scheduler.running:
        # Import the tasks here to avoid circular imports
        from .tasks import send_due_date_reminders

        # Add the job to the scheduler
        scheduler.add_job(
            func=lambda: send_due_date_reminders(app), # Pass the app instance
            trigger='cron',
            hour=8, # Run at 8 AM UTC
            minute=1,
            id='due_date_reminders',
            replace_existing=True
        )
        scheduler.start()
        # Ensure the scheduler shuts down when the app exits
        atexit.register(lambda: scheduler.shutdown())
        app.logger.info("APScheduler started and reminder job added.")

    return app