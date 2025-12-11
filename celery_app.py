import os
from celery import Celery
from flask import Flask

def make_celery(app):
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend
    )

    celery.conf.update(app.config)

    # -------
    # Make Celery tasks run INSIDE Flask app context
    # -------
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# --------------------------------------
# Initialize Celery with your Flask app
# --------------------------------------
def create_celery():
    # local import to avoid circular import
    from app import app
    return make_celery(app)

celery = create_celery()
