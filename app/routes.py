from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .models import User, Todo 
from extensions import db
from .forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, TodoForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message, Mail
from flask import current_app
from datetime import datetime, timezone

main_bp = Blueprint('main_bp', __name__)
mail = Mail()

@main_bp.route('/')
def index():
    return render_template("index.html")

# --- Auth Routes ---

# Signup
@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))

    form = RegistrationForm()

    if request.method == 'GET' and 'email' in request.args:
        form.email.data = request.args.get('email')

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash(f'Account created for {username}!', 'success')
        return redirect(url_for('main_bp.signin'))

    return render_template('signup.html', form=form)

# Login
@main_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = db.session.execute(db.select(User).filter((User.username == username_or_email) | (User.email == username_or_email))).scalar_one_or_none()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember_me)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.user_dashboard'))

        else:
            flash('Login Unsuccessful. Please check username/email and password', 'danger')

    return render_template('signin.html', form=form)

# Logout
@main_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))

# User Dashboard (Read To-dos)
@main_bp.route('/dashboard')
@login_required
def user_dashboard():
    todos = db.session.execute(db.select(Todo).filter_by(author=current_user).order_by(Todo.created_at.desc())).scalars().all()
    return render_template('user_dashboard.html', todos=todos)

# Request Password Reset
@main_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        if user:
            token = user.get_reset_token()
            msg = Message('Password Reset Request', sender=current_app.config['MAIL_DEFAULT_SENDER'], recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('main_bp.reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.', 'info')
        else:
            flash('No account found with that email address.', 'danger')
        return redirect(url_for('main_bp.signin'))
    return render_template('reset_request.html', title='Reset Password', form=form)

# Reset Password with Token
@main_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main_bp.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        user.reset_token = None  # Clear the token after use
        user.reset_token_expiration = None  # Clear the expiration after use
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('main_bp.signin'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# --- To-do Routes ---

# Create To-do
@main_bp.route('/todo/new', methods=['GET', 'POST'])
@login_required
def new_todo():
    form = TodoForm()
    if form.validate_on_submit():
        todo = Todo(
            description=form.description.data,
            due_date=form.due_date.data,
            status=form.status.data,
            author=current_user
        )
        db.session.add(todo)
        db.session.commit()
        flash('Your to-do has been created!', 'success')
        return redirect(url_for('main_bp.user_dashboard'))
    return render_template('create_todo.html', title='New To-do', form=form)

# Update To-do
@main_bp.route('/todo/<int:todo_id>/update', methods=['GET', 'POST'])
@login_required
def update_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        abort(404) # Return 404 if to-do not found
    if todo.author != current_user:
        abort(403) # Return 403 if user is not the author

    form = TodoForm()
    if form.validate_on_submit():
        todo.description = form.description.data
        todo.due_date = form.due_date.data
        todo.status = form.status.data
        db.session.commit()
        flash('Your to-do has been updated!', 'success')
        return redirect(url_for('main_bp.user_dashboard'))
    elif request.method == 'GET':
        form.description.data = todo.description
        form.due_date.data = todo.due_date
        form.status.data = todo.status
    return render_template('create_todo.html', title='Update To-do', form=form) # Reuse create_todo template

# Delete To-do
@main_bp.route('/todo/<int:todo_id>/delete', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        abort(404) # Return 404 if to-do not found
    if todo.author != current_user:
        abort(403) # Return 403 if user is not the author

    db.session.delete(todo)
    db.session.commit()
    flash('Your to-do has been deleted!', 'success')
    return redirect(url_for('main_bp.user_dashboard'))