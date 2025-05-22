from extensions import db
from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    todos = db.relationship('Todo', backref='author', lazy='dynamic')
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': self.id})
        self.reset_token = token
        # Store as offset-aware datetime in UTC
        self.reset_token_expiration = datetime.now(timezone.utc) + timedelta(seconds=expires_sec)
        db.session.commit()
        return token

    @staticmethod
    def verify_reset_token(token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=1800) # itsdangerous handles expiration check here
            user_id = data['user_id']
        except Exception: # Catches expired token or bad signature
            return None

        user = db.session.get(User, user_id)

        # Ensure user exists and the token matches the one stored in the database
        if user is None or user.reset_token != token:
            return None

        # Now, explicitly check the expiration time stored in the database
        # This is a secondary check, primarily to ensure the token hasn't been invalidated

        expiration_time_from_db = user.reset_token_expiration

        # If expiration_time_from_db is None (e.g., token already used and cleared), treat as expired/invalid
        if expiration_time_from_db is None:
            return None

        # Ensure the expiration_time_from_db is timezone-aware (UTC) before comparison
        if expiration_time_from_db.tzinfo is None or expiration_time_from_db.tzinfo.utcoffset(expiration_time_from_db) is None:
            expiration_time_from_db = expiration_time_from_db.replace(tzinfo=timezone.utc)

        if expiration_time_from_db < datetime.now(timezone.utc):
            return None

        return user


class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    # Fields for categories/tags and priority
    tags = db.Column(db.String(255), nullable=True)  # Stores comma-separated tags
    priority = db.Column(db.String(20), default='medium', nullable=False) # 'low', 'medium', 'high'

    def __repr__(self):
        return f'<Todo {self.description}>'