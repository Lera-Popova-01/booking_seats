from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей в системе."""

    USER = 'user'
    MANAGER = 'manager'
    ADMIN = 'admin'


class BookingStatus(StrEnum):
    """Статусы бронирования."""

    BOOKING = 'booking'
    CANCELED = 'canceled'
    ACTIVE = 'active'
