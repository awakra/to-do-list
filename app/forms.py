from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from .models import User, Todo 
from extensions import db
from flask_login import current_user
from datetime import date

class RegistrationForm(FlaskForm):
    """User signup form."""
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=2, max=80)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = db.session.execute(db.select(User).filter_by(username=username.data)).scalar_one_or_none()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = db.session.execute(db.select(User).filter_by(email=email.data)).scalar_one_or_none()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    """User signin form."""
    username_or_email = StringField(
        'Username or Email',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

class RequestResetForm(FlaskForm):
    """Request password recovery form."""
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = db.session.execute(db.select(User).filter_by(email=email.data)).scalar_one_or_none()
        if user is None:
            raise ValidationError('There is no account with that email address.')

class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
    
class TodoForm(FlaskForm):
    """Form for creating and updating To-do items."""
    description = TextAreaField(
        'Description',
        validators=[DataRequired(), Length(max=200)]
    )
    due_date = DateField(
        'Due Date',
        format='%Y-%m-%d', # Specify the date format
        validators=[], # Make due date optional
        render_kw={"placeholder": "YYYY-MM-DD"} # Add a placeholder
    )
    status = SelectField(
        'Status',
        choices=[('pending', 'Pending'), ('complete', 'Complete')],
        validators=[DataRequired()]
    )
    # Fields for tags and priority
    tags = StringField(
        'Tags (comma separated)',
        validators=[Length(max=255)],
        render_kw={"placeholder": "work, personal, urgent"}
    )
    priority = SelectField(
        'Priority',
        choices=[
            ('low', 'Low'), 
            ('medium', 'Medium'), 
            ('high', 'High')
        ],
        default='medium',
        validators=[DataRequired()]
    )
    submit = SubmitField('Save To-do')