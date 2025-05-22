# To-Do Tracker

A simple and professional web application to organize, manage, and track your to-do tasks efficiently. Built with Flask, this app supports user authentication, task creation, editing, completion, and calendar visualization, along with email notifications and password reset functionality.

---

## Features

- **User Authentication:** Secure signup, login, logout, and password reset via email.
- **Task Management:** Create, update, delete, and mark tasks as complete.
- **Task Organization:** Assign priorities, tags, and due dates to tasks.
- **Dashboard:** Personalized user dashboard showing pending tasks.
- **Calendar View:** Visualize tasks on a calendar with color-coded priorities.
- **Completed Tasks History:** View and restore completed tasks.
- **Email Notifications:** Automated reminders for tasks due soon.
- **Security:** CSRF protection and secure password hashing.

---

## Technology Stack

- Python 3.9+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- Flask-Mail
- APScheduler
- SQLite (default, configurable for other databases)
- Bootstrap 5 (frontend styling)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/awakra/to-do-list.git
cd todo-tracker
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

Create a `.env` file. Example:

```bash
# Flask Secret Key - Used for session management and security
SECRET_KEY='your_super_secret_and_unique_key_here'

# Database Configuration
# For Development (SQLite)
# DEV_DATABASE_URL='sqlite:///instance/dev.db'
# For Production (Example PostgreSQL)
# DATABASE_URL='postgresql://user:password@host:port/database_name'

# Flask Configuration (development or production)
FLASK_CONFIG='development'

# Email Configuration (for Flask-Mail)
MAIL_SERVER='smtp.gmail.com'
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=''
MAIL_PASSWORD=''
MAIL_DEFAULT_SENDER='mail@gmail.com'
```

### 5. Initialize the database

```bash
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
```

### 6. Run the application

```bash
flask run
```

---

## Usage

- Access the app at [http://localhost:5000](http://localhost:5000)
- Register a new account or sign in
- Create, edit, complete, and delete your to-do tasks
- View tasks on the calendar
- Receive email reminders for upcoming tasks
- Reset your password via email if needed

---

## Project Structure

```
todo-tracker/
│
├── app/
│   ├── __init__.py         # Application factory and app initialization
│   ├── routes.py           # Flask routes and view functions
│   ├── models.py           # Database models for User and Todo
│   ├── forms.py            # WTForms for user input validation
│   ├── tasks.py            # Background tasks such as sending email reminders
│   ├── extensions.py       # Flask extensions initialization
│   ├── templates/          # HTML templates using Jinja2
│   └── static/             # Static files (CSS, JS, images)
│
├── config.py               # Configuration classes
├── run.py                  # Entry point to run the app
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```
