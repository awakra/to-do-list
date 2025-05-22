from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from .models import User, Todo
from extensions import db, mail
from .forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, TodoForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from datetime import datetime, timezone

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    return render_template("index.html")

# --- Auth Routes ---

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

@main_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = db.session.execute(
            db.select(User).filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            )
        ).scalar_one_or_none()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember_me)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.user_dashboard'))

        else:
            flash('Login Unsuccessful. Please check username/email and password', 'danger')

    return render_template('signin.html', form=form)

@main_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))

# --- User Dashboard ---

@main_bp.route('/dashboard')
@login_required
def user_dashboard():
    todos = db.session.execute(
        db.select(Todo)
        .filter(Todo.author == current_user, Todo.status != 'complete')
        .order_by(Todo.created_at.desc())
    ).scalars().all()
    return render_template('user_dashboard.html', todos=todos)

# --- Password Reset Routes ---

@main_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        if user:
            token = user.get_reset_token()
            msg = Message(
                'Password Reset Request',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
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
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('main_bp.signin'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# --- To-do Routes ---

@main_bp.route('/todo/new', methods=['GET', 'POST'])
@login_required
def new_todo():
    form = TodoForm()
    if form.validate_on_submit():
        todo = Todo(
            description=form.description.data,
            due_date=form.due_date.data,
            status=form.status.data,
            tags=form.tags.data,
            priority=form.priority.data,
            author=current_user
        )
        db.session.add(todo)
        db.session.commit()
        flash('Your to-do has been created!', 'success')
        return redirect(url_for('main_bp.user_dashboard'))
    return render_template('create_todo.html', title='New To-do', form=form)

@main_bp.route('/todo/<int:todo_id>/update', methods=['GET', 'POST'])
@login_required
def update_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        abort(404)
    if todo.author != current_user:
        abort(403)

    form = TodoForm()
    if form.validate_on_submit():
        todo.description = form.description.data
        todo.due_date = form.due_date.data
        todo.status = form.status.data
        todo.tags = form.tags.data
        todo.priority = form.priority.data
        db.session.commit()
        flash('Your to-do has been updated!', 'success')
        return redirect(url_for('main_bp.user_dashboard'))
    elif request.method == 'GET':
        form.description.data = todo.description
        form.due_date.data = todo.due_date
        form.status.data = todo.status
        form.tags.data = todo.tags
        form.priority.data = todo.priority
    return render_template('create_todo.html', title='Update To-do', form=form)

@main_bp.route('/todo/<int:todo_id>/delete', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        abort(404)
    if todo.author != current_user:
        abort(403)

    db.session.delete(todo)
    db.session.commit()
    flash('Your to-do has been deleted!', 'success')
    return redirect(url_for('main_bp.user_dashboard'))

@main_bp.route('/todo/<int:todo_id>/complete', methods=['POST'])
@login_required
def complete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        abort(404)
    if todo.author != current_user:
        abort(403)

    todo.status = 'complete'
    db.session.commit()
    flash('Task marked as complete.', 'success')
    return redirect(url_for('main_bp.user_dashboard'))

# --- Calendar Routes ---

@main_bp.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html', title='Calendar View')

@main_bp.route('/api/todos_calendar')
@login_required
def todos_calendar_api():
    todos = db.session.execute(
        db.select(Todo)
        .filter(Todo.author == current_user, Todo.status != 'complete')
        .order_by(Todo.due_date.asc())
    ).scalars().all()

    events = []
    for todo in todos:
        if todo.due_date:
            event_color = '#3788d8'
            if todo.priority == 'high':
                event_color = '#dc3545'
            elif todo.priority == 'medium':
                event_color = '#ffc107'
            elif todo.priority == 'low':
                event_color = '#17a2b8'

            events.append({
                'id': todo.id,
                'title': todo.description,
                'start': todo.due_date.isoformat(),
                'allDay': True,
                'url': url_for('main_bp.update_todo', todo_id=todo.id),
                'color': event_color,
                'extendedProps': {
                    'status': todo.status,
                    'tags': todo.tags,
                    'priority': todo.priority
                }
            })
    return jsonify(events)

# --- Completed Todos History Routes ---

@main_bp.route('/completed_todos')
@login_required
def completed_todos_history():
    completed_todos = db.session.execute(
        db.select(Todo).filter_by(author=current_user, status='complete').order_by(Todo.created_at.desc())
    ).scalars().all()

    total_completed = len(completed_todos)
    completed_by_month = {}
    for todo in completed_todos:
        if todo.created_at:
            month_year = todo.created_at.strftime('%Y-%m')
            completed_by_month[month_year] = completed_by_month.get(month_year, 0) + 1

    return render_template(
        'completed_todos.html',
        title='Completed To-dos History',
        completed_todos=completed_todos,
        total_completed=total_completed,
        completed_by_month=completed_by_month
    )

@main_bp.route('/todo/<int:todo_id>/restore', methods=['POST'])
@login_required
def restore_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo is None:
        abort(404)
    if todo.author != current_user:
        abort(403)

    if todo.status == 'complete':
        todo.status = 'pending'
        db.session.commit()
        flash('To-do item restored successfully!', 'success')
    else:
        flash('This to-do item is not marked as complete.', 'warning')

    return redirect(url_for('main_bp.completed_todos_history'))