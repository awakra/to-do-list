from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User
from extensions import db
from .forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    return render_template("index.html")

# --- Auth Routes---
@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.user_dashboard'))

    form = RegistrationForm()

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

@main_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main_bp.index'))


@main_bp.route('/dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')