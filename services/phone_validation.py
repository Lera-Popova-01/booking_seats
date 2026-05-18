from typing import Optional

from src.services.constants import PHONE_INVALID_CHARS, PHONE_PATTERN


def validate_phone_number(phone: Optional[str]) -> Optional[str]:
    """Валидация и нормализация номера телефона."""
    if phone is None:
        return phone
    cleaned = PHONE_INVALID_CHARS.sub('', phone)
    if not PHONE_PATTERN.match(cleaned):
        raise ValueError(
            'Неверный формат телефона. '
            'Ожидается: +79991234567 или 89991234567',
        )
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    elif not cleaned.startswith('+'):
        cleaned = '+' + cleaned

    return cleaned
