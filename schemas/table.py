from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.cafe import CafeShortInfo
from src.services.constants import SEAT_GT, SEAT_LE


class TableBase(BaseModel):
    """Базовая схема стола."""

    description: str = Field(..., description='Описание стола')
    seat_number: int = Field(
        ...,
        description='Количество мест за столом',
    )

    @field_validator('description')
    @classmethod
    def validate_description(cls, descr: str) -> str:
        """Проверяем описание поля на пустоту."""
        if not descr or not descr.strip():
            raise ValueError('Описание не должно быть пустым')
        return descr.strip()

    @field_validator('seat_number')
    @classmethod
    def validate_seat_number(cls, value: int) -> int:
        """Проверяем количество мест."""
        if value <= SEAT_GT:
            raise ValueError('Количество мест должно быть больше 0')
        if value > SEAT_LE:
            raise ValueError('Количество мест не может быть больше 20')
        return value


class TableCreate(TableBase):
    """Схема создания нового стола."""

    cafe_id: int = Field(..., description='ID кафе, к которому относится стол')


class TableUpdate(BaseModel):
    """Схема обновления данных стола."""

    cafe_id: Optional[int] = Field(None, description='ID кафе этого стола')
    description: Optional[str] = Field(None, description='Описание стола')
    seat_number: Optional[int] = Field(
        None,
        description='Количество мест за столом',
    )
    is_active: Optional[bool] = Field(None, description='Активен стол или нет')

    @field_validator('description')
    @classmethod
    def validate_description(cls, descr: Optional[str]) -> Optional[str]:
        """Проверяем описание стола на пустоту."""
        if descr is None:
            return descr
        if not descr.strip():
            raise ValueError('Описание не должно быть пустым')
        return descr.strip()

    @field_validator('seat_number')
    @classmethod
    def validate_seat_number(cls, value: Optional[int]) -> Optional[int]:
        """Проверяем количество мест."""
        if value is None:
            return value
        if value <= SEAT_GT:
            raise ValueError('Количество мест должно быть больше 0')
        if value > SEAT_LE:
            raise ValueError('Количество мест не может быть больше 20')
        return value


class TableShortInfo(TableBase):
    """Краткая информация о столе."""

    id: int = Field(..., description='ID стола')

    model_config = ConfigDict(extra='forbid', from_attributes=True)


class TableInfo(TableBase):
    """Полная информация о столе."""

    id: int = Field(..., description='ID стола')
    cafe: CafeShortInfo
    is_active: bool = Field(..., description='Активен стол или нет')
    created_at: datetime = Field(
        ...,
        description='Дата и время создания записи',
    )
    updated_at: datetime = Field(
        ...,
        description='Дата и время последнего обновления записи',
    )

    model_config = ConfigDict(extra='forbid', from_attributes=True)
