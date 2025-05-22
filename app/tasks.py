from datetime import datetime, timedelta, timezone
from flask_mail import Message
from flask import current_app, url_for
from extensions import db 
from .models import Todo, User 

def send_due_date_reminders(app):
    """
    Sends email reminders for tasks due within the next 24 hours.
    This function runs in a background thread via APScheduler.
    """
    with app.app_context():
        now_utc = datetime.now(timezone.utc)
        reminder_window_start = now_utc
        reminder_window_end = now_utc + timedelta(days=1)

        # Query for todos that are pending and have a due_date within the reminder window
        # Ensure due_date is not None and is within the next 24 hours
        todos_due_soon = db.session.execute(
            db.select(Todo).filter(
                Todo.status == 'pending',
                Todo.due_date.isnot(None),
                Todo.due_date >= reminder_window_start,
                Todo.due_date < reminder_window_end
            )
        ).scalars().all()

        if not todos_due_soon:
            app.logger.info("No pending todos due in the next 24 hours found for reminders.")
            return

        app.logger.info(f"Found {len(todos_due_soon)} todos due soon. Sending reminders...")

        for todo in todos_due_soon:
            user = todo.author # Access the associated user via the relationship
            if user and user.email:
                try:
                    msg = Message(
                        f'Reminder: Your To-do "{todo.description}" is due soon!',
                        sender=current_app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[user.email]
                    )
                    due_date_str = todo.due_date.strftime('%Y-%m-%d') if todo.due_date else 'N/A'
                    msg.body = f'''
Hello {user.username},

This is a friendly reminder that your to-do item:
"{todo.description}"
is due on {due_date_str}.

Priority: {todo.priority.capitalize()}
Status: {todo.status.capitalize()}
Tags: {todo.tags if todo.tags else 'None'}

Don't forget to complete it!

You can view and manage your tasks here:
{url_for('main_bp.user_dashboard', _external=True)}

Best regards,
Your To-do App Team
'''
                    current_app.mail.send(msg)
                    app.logger.info(f"Reminder sent for todo ID {todo.id} to {user.email}")
                except Exception as e:
                    app.logger.error(f"Failed to send reminder for todo ID {todo.id} to {user.email}: {e}")
            else:
                app.logger.warning(f"Could not send reminder for todo ID {todo.id}: User or email not found.")