from celery_app import celery
from flask_mail import Message
from app import mail, db
from app.models import Lead

@celery.task(name="task.add")
def task_add(a, b):
    return a + b

@celery.task(name="task.send_email")
def task_send_email(to, subject, body):
    try:
        msg = Message(subject=subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        return {"status": "sent", "to": to}
    except Exception as e:
        return {"status": "error", "error": str(e)}
