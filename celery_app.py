import os
from celery import Celery
from dotenv import load_dotenv
load_dotenv()
# Celery config (Redis URLs passed via env vars)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")

celery = Celery(
    "educall",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# optional configs
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata"
)


# Allow tasks to use Flask App Context
from app import app

class FlaskContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return super().__call__(*args, **kwargs)

celery.Task = FlaskContextTask
