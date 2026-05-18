import logging
import smtplib
from email.message import EmailMessage

from src.core.config import settings

logger = logging.getLogger(__name__)


def send_booking_reminder_email(
    recipient_email: str,
    subject: str,
    body: str,
) -> bool:
    """Отправить email-напоминание о бронировании."""
    if not settings.smtp_host or not settings.smtp_from_email:
        logger.warning(
            'Email не отправлен: SMTP_HOST или SMTP_FROM_EMAIL не настроены',
        )
        return False

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = settings.smtp_from_email
    message['To'] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(
                    settings.smtp_user,
                    settings.smtp_password.get_secret_value(),
                )
            smtp.send_message(message)
    except smtplib.SMTPException:
        logger.exception(
            'Ошибка SMTP при отправке напоминания на email %s',
            recipient_email,
        )
        return False

    return True
