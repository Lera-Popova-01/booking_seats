from datetime import date
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.models.enums import BookingStatus
from src.schemas.base import BaseShema
from src.schemas.cafe import CafeShortInfo
from src.schemas.table import TableShortInfo
from src.schemas.time_slot import TimeSlotShortInfo
from src.schemas.user import UserShortInfo
from src.services.constants import (
    MIN_NUMBER,
    NOTE_MAX_LENGTH,
)


class BookingBase(BaseModel):
    """Базовая схема бронирования."""

    guest_number: Optional[int] = Field(None, ge=MIN_NUMBER)
    note: Optional[str] = Field(None, max_length=NOTE_MAX_LENGTH)
    booking_date: Optional[date] = None

    @field_validator('booking_date')
    @classmethod
    def validate_booking_date(cls, value: Optional[date]) -> Optional[date]:
        """Запрет бронирования на прошедшие даты."""
        if value is not None and value < date.today():
            raise ValueError(
                'Нельзя забронировать дату предшествующую текущей',
            )
        return value

    @field_validator('guest_number')
    @classmethod
    def validate_guest_number(cls, value: Optional[int]) -> Optional[int]:
        """Проверка количества гостей."""
        if value is not None and value < MIN_NUMBER:
            raise ValueError('Количество гостей должно быть не менее 1')
        return value

    @field_validator('note')
    @classmethod
    def validate_note(cls, value: Optional[str]) -> Optional[str]:
        """Валидация заметки."""
        if value is not None and len(value.strip()) == 0:
            return None
        return value

    model_config = ConfigDict(extra='forbid', from_attributes=True)


class BookingCreate(BookingBase):
    """Схема создания бронирования."""

    cafe_id: int
    tables_id: List[int] = Field(..., min_length=MIN_NUMBER)
    slots_id: List[int] = Field(..., min_length=MIN_NUMBER)
    booking_date: date
    guest_number: int = Field(..., ge=MIN_NUMBER)

    @model_validator(mode='after')
    def validate_required_fields(self) -> 'BookingCreate':
        """Проверка наличия обязательных полей."""
        if not self.booking_date:
            raise ValueError('Необходимо указать дату бронирования')
        if not self.guest_number:
            raise ValueError('Необходимо указать количество гостей')
        if not self.tables_id:
            raise ValueError('Необходимо указать хотя бы один стол')
        if not self.slots_id:
            raise ValueError('Необходимо указать хотя бы один слот')
        return self

    @field_validator('tables_id')
    @classmethod
    def validate_tables_id(cls, value: List[int]) -> List[int]:
        """Проверка ID столов на уникальность."""
        if len(set(value)) != len(value):
            raise ValueError('ID столов не должны повторяться')
        return value

    @field_validator('slots_id')
    @classmethod
    def validate_slots_id(cls, value: List[int]) -> List[int]:
        """Проверка ID слотов на уникальность."""
        if len(set(value)) != len(value):
            raise ValueError('ID слотов не должны повторяться')
        return value


class BookingUpdate(BookingBase):
    """Схема обновления бронирования."""

    cafe_id: Optional[int] = None
    tables_id: Optional[List[int]] = Field(None, min_length=MIN_NUMBER)
    slots_id: Optional[List[int]] = Field(None, min_length=MIN_NUMBER)
    status: Optional[BookingStatus] = None
    booking_date: Optional[date] = None
    is_active: Optional[bool] = None

    @field_validator('tables_id')
    @classmethod
    def validate_tables_id(
        cls, value: Optional[List[int]],
    ) -> Optional[List[int]]:
        """Проверка ID столов на уникальность."""
        if value and len(set(value)) != len(value):
            raise ValueError('ID столов не должны повторяться')
        return value

    @field_validator('slots_id')
    @classmethod
    def validate_slots_id(
        cls, value: Optional[List[int]],
    ) -> Optional[List[int]]:
        """Проверка ID слотов на уникальность."""
        if value and len(set(value)) != len(value):
            raise ValueError('ID слотов не должны повторяться')
        return value

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'BookingUpdate':
        """Проверить, что для обновления передано хотя бы одно поле."""
        values = self.model_dump(exclude_unset=True)
        if not values:
            raise ValueError('Не указано хотя бы одно поле для обновления')
        return self

    model_config = ConfigDict(extra='forbid', from_attributes=True)


class BookingInfo(BaseShema):
    """Схема информации о брони."""

    user: UserShortInfo
    cafe: CafeShortInfo
    tables: List[TableShortInfo]
    slots: List[TimeSlotShortInfo]
    guest_number: int
    note: Optional[str] = None
    status: BookingStatus
    booking_date: date
