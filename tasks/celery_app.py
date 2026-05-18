from celery import Celery

from src.core.config import settings

celery_app = Celery(
    'cafe_booking',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    timezone=settings.celery_timezone,
    enable_utc=True,
)

import src.notifications.tasks  # noqa: E402, F401
import src.tasks.reminders  # noqa: E402, F401
