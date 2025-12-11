from celery_app import celery
import time

@celery.task
def test_add(x, y):
    # Tiny fake "heavy work"
    time.sleep(3)
    return x + y
