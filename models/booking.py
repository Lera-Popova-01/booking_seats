from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import Table as SQLAlchemyTable
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.db import Base
from src.models.cafe import Cafe
from src.models.enums import BookingStatus
from src.models.table import Table
from src.models.time_slot import TimeSlot
from src.models.user import User
from src.services.constants import (
    MIN_NUMBER,
    NOTE_MAX_LENGTH,
    STATUS_MAX_LENGTH,
)

booking_tables_slots = SQLAlchemyTable(
    'booking_tables_slots',
    Base.metadata,
    Column('booking_id', ForeignKey('booking.id'), primary_key=True),
    Column('table_id', ForeignKey('table.id'), primary_key=True),
    Column('slot_id', ForeignKey('timeslot.id'), primary_key=True),
    Column('booking_date', Date, nullable=False),
    UniqueConstraint(
        'table_id', 'slot_id', 'booking_date',
        name='uq_booking_item_table_slot_date',
    ),
)


class Booking(Base):
    """Модель бронирования."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey('users.id'), nullable=False, index=True,
    )
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'), nullable=False, index=True,
    )
    guest_number: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(NOTE_MAX_LENGTH))
    status: Mapped[str] = mapped_column(
        String(STATUS_MAX_LENGTH),
        default=BookingStatus.BOOKING.value,
        nullable=False,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    reminder_minutes_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='60',
    )
    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    user: Mapped['User'] = relationship('User')
    cafe: Mapped['Cafe'] = relationship('Cafe')
    tables: Mapped[List['Table']] = relationship(
        'Table',
        secondary=booking_tables_slots,
        lazy="selectin",
        viewonly=True,
    )
    slots: Mapped[List['TimeSlot']] = relationship(
        'TimeSlot',
        secondary=booking_tables_slots,
        lazy="selectin",
        viewonly=True,
    )

    __table_args__ = (
        CheckConstraint(
            'guest_number > 0', name='check_guest_number_positive',
        ),
    )

    @validates('guest_number')
    def validate_guest_number(self, key: str, value: int) -> int:
        """Проверка количества гостей."""
        if value < MIN_NUMBER:
            raise ValueError('Количество гостей должно быть не менее 1')
        return value

    @validates('booking_date')
    def validate_booking_date(self, key: str, value: date) -> date:
        """Валидация даты бронирования."""
        if value < date.today():
            raise ValueError('Нельзя забронировать на прошедшую дату')
        return value

    @validates('note')
    def validate_note(self, key: str, value: str | None) -> str | None:
        """Валидация заметки."""
        if value is not None:
            if len(value) > NOTE_MAX_LENGTH:
                raise ValueError('Заметка не может превышать 500 символов')
            if len(value.strip()) == 0:
                return None
        return value
