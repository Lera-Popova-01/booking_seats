import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.db import AsyncSessionLocal, engine
from src.models import Booking, BookingStatus
from src.services.notification_delivery import send_booking_reminder_email
from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_booking_timezone() -> ZoneInfo:
    """Определение часового пояса для расчёта времени напоминаний."""
    try:
        return ZoneInfo(settings.booking_timezone)
    except Exception:
        logger.warning(
            'Некорректный часово пояс BOOKING_TIMEZONE=%s, используем UTC',
            settings.booking_timezone,
        )
        return ZoneInfo('UTC')


def build_booking_reminder_eta(booking: Booking) -> datetime | None:
    """Собрать время запуска напоминания по бронированию."""
    if not booking.reminder_minutes_before or not booking.slots:
        return None

    booking_timezone = _get_booking_timezone()
    first_slot = min(booking.slots, key=lambda slot: slot.start_time)
    booking_start = datetime.combine(
        booking.booking_date,
        first_slot.start_time,
        tzinfo=booking_timezone,
    )
    return booking_start - timedelta(
        minutes=booking.reminder_minutes_before,
    )


def booking_reminder_task_id(booking_id: int) -> str:
    """Детерминированный идентификатор Celery-задачи."""
    return f'booking-reminder-{booking_id}'


async def _send_booking_reminder(booking_id: int) -> None:
    """Проверить актуальность брони и залогировать напоминание."""
    async with AsyncSessionLocal() as session:
        query = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.slots),
                selectinload(Booking.user),
                selectinload(Booking.cafe),
            )
        )
        result = await session.execute(query)
        booking = result.scalars().first()

        if booking is None or not booking.is_active:
            logger.info(
                'Напоминание не отправлено: бронирование %s не найдено '
                'или неактивно',
                booking_id,
            )
            return

        if booking.status != BookingStatus.ACTIVE.value:
            logger.info(
                'Напоминание не отправлено: бронирование %s имеет статус %s',
                booking_id,
                booking.status,
            )
            return

        if booking.reminder_sent_at is not None:
            logger.info(
                'Напоминание по бронированию %s уже было отправлено',
                booking_id,
            )
            return

        eta = build_booking_reminder_eta(booking)
        if eta is None:
            logger.info(
                'Напоминание не настроено для бронирования %s',
                booking_id,
            )
            return

        now_utc = datetime.now(timezone.utc)
        eta_utc = eta.astimezone(timezone.utc)

        if now_utc + timedelta(minutes=1) < eta_utc:
            send_booking_reminder.apply_async(
                args=[booking.id],
                eta=eta_utc,
                task_id=booking_reminder_task_id(booking.id),
            )
            logger.info(
                'Задача напоминания %s запущена раньше срока, '
                'перепланирована на %s',
                booking_id,
                eta_utc.isoformat(),
            )
            return

        sent = _deliver_booking_reminder(booking)
        if not sent:
            logger.warning(
                'Напоминание по бронированию %s не отправлено: '
                'нет доступного канала доставки',
                booking.id,
            )
            return

        booking.reminder_sent_at = datetime.utcnow()
        session.add(booking)
        await session.commit()


def _deliver_booking_reminder(booking: Booking) -> bool:
    """Отправить напоминание пользователю по доступному каналу."""
    user = booking.user
    if user.email:
        subject = 'Напоминание о бронировании'
        body = (
            f'Здравствуйте, {user.username}!\n\n'
            f'Напоминаем о вашем бронировании в кафе "{booking.cafe.name}" '
            f'на {booking.booking_date}.\n'
            f'Количество гостей: {booking.guest_number}.\n'
        )
        email_sent = send_booking_reminder_email(
            recipient_email=user.email,
            subject=subject,
            body=body,
        )
        if email_sent:
            logger.info(
                'Отправлено email-напоминание по бронированию %s '
                'пользователю %s (%s)',
                booking.id,
                user.username,
                user.id,
            )
            return True
    return False


@celery_app.task(name='booking.send_reminder')
def send_booking_reminder(booking_id: int) -> None:
    """Celery-обертка над асинхронной отправкой напоминания."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_booking_reminder(booking_id))
        loop.run_until_complete(engine.dispose())
    finally:
        loop.close()
        asyncio.set_event_loop(None)
