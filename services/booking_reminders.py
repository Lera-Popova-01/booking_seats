import logging
from datetime import datetime, timezone

from src.models import Booking
from src.models.booking import BookingStatus
from src.tasks.reminders import (
    booking_reminder_task_id,
    build_booking_reminder_eta,
    send_booking_reminder,
)

logger = logging.getLogger(__name__)


def schedule_booking_reminder(booking: Booking) -> None:
    """Поставить задачу напоминания в очередь, если она актуальна."""
    if (
        booking.status != BookingStatus.ACTIVE.value
        or not booking.is_active
        or booking.reminder_sent_at is not None
    ):
        return

    eta = build_booking_reminder_eta(booking)
    if eta is None or eta <= datetime.now(timezone.utc):
        return

    try:
        send_booking_reminder.apply_async(
            args=[booking.id],
            eta=eta.astimezone(timezone.utc),
            task_id=booking_reminder_task_id(booking.id),
        )
    except Exception:
        logger.exception(
            'Не удалось поставить напоминание для бронирования %s в очередь',
            booking.id,
        )
