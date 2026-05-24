from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_email(to_email, task_name, deadline):
    sender = os.environ.get('EMAIL_ADDRESS')
    password = os.environ.get('EMAIL_PASSWORD')
    if not sender or not password:
        print(f"[reminders] EMAIL_ADDRESS or EMAIL_PASSWORD not set — skipping email to {to_email}")
        return
    msg = MIMEText(f"Reminder: Your task '{task_name}' is due on {deadline}")
    msg['Subject'] = 'Trackr Reminder'
    msg['From'] = sender
    msg['To'] = to_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
def check_reminders(db, Todo, app):
    with app.app_context():
        now = datetime.now()
        due_tasks = Todo.query.filter(Todo.reminder_time <= now, Todo.message_delivered==False).all()
        for task in due_tasks:
            send_email(task.email, task.task_name, task.deadline)
            task.message_delivered = True
            db.session.commit()