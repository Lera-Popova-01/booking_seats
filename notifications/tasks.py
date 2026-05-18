from typing import Any, Dict, Optional

from celery.utils.log import get_task_logger

from src.core.config import settings
from src.services.notification_delivery import send_booking_reminder_email
from src.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task
def debug_task(message: str) -> None:
    """Тестовая задача для проверки Celery."""
    logger.info('Debug task received message: %s', message)


@celery_app.task
def send_admin_booking_created(booking_id: int) -> None:
    """Уведомление администратора о создании бронирования."""
    logger.info('New booking created. Booking ID: %s', booking_id)
    admin_email = settings.first_superuser_email
    if admin_email:
        send_booking_reminder_email(
            recipient_email=admin_email,
            subject=f'Новое бронирование #{booking_id}',
            body=f'Создано новое бронирование #{booking_id} в системе.',
        )


@celery_app.task
def send_admin_booking_updated(
    booking_id: int,
    changes: Optional[Dict[str, Any]] = None,
) -> None:
    """Уведомление администратора об изменении бронирования."""
    admin_email = settings.first_superuser_email
    if changes is None:
        logger.info('Booking updated. Booking ID: %s', booking_id)
        return
    logger.info(
        'Booking updated. Booking ID: %s, changes: %s',
        booking_id,
        changes,
    )
    if admin_email:
        send_booking_reminder_email(
            recipient_email=admin_email,
            subject=f'Обновление бронирования #{booking_id}',
            body=f'Бронирование #{booking_id} было обновлено в системе.',
        )
