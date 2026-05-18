from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.base import BaseShema
from src.schemas.user import UserShortInfo
from src.services.constants import (
    MIN_LENGTH,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)
from src.services.phone_validation import validate_phone_number


class CafeBase(BaseModel):
    """Базовая схема кафе."""

    name: str = Field(..., min_length=MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    address: str = Field(..., min_length=MIN_LENGTH)
    phone: str = Field(..., min_length=MIN_LENGTH, max_length=PHONE_MAX_LENGTH)
    description: str = Field(..., min_length=MIN_LENGTH)
    photo: Optional[UUID] = Field(None)

    model_config = ConfigDict(extra='forbid')


class CafeInfo(CafeBase, BaseShema):
    """Схема для ответа с полной информацией о кафе."""

    managers: Optional[list[UserShortInfo]] = None


class CafeCreate(CafeBase):
    """Схема для создания нового кафе."""

    managers_id: list[UUID] = Field(..., title='Менеджеры кафе')

    @field_validator('phone')
    @classmethod
    def validate_phone_number(cls, phone: str) -> str:
        """Валидация номера телефона при создании кафе."""
        return validate_phone_number(phone)


class CafeShortInfo(CafeBase):
    """Схема для ответа с краткой информацией о кафе."""

    id: int


class CafeUpdate(BaseModel):
    """Схема для обновления кафе."""

    name: Optional[str] = Field(
        None, min_length=MIN_LENGTH, max_length=NAME_MAX_LENGTH,
    )
    address: Optional[str] = Field(None, min_length=MIN_LENGTH)
    phone: Optional[str] = Field(
        None, min_length=11, max_length=PHONE_MAX_LENGTH,
    )
    description: Optional[str] = Field(None, min_length=MIN_LENGTH)
    photo_id: Optional[UUID] = Field(None)
    managers_id: Optional[list[UUID]] = Field(None)
    is_active: Optional[bool] = Field(None)

    @field_validator('phone')
    @classmethod
    def validate_phone_number(cls, phone: Optional[str]) -> Optional[str]:
        """Валидация номера телефона при изменении кафе."""
        return validate_phone_number(phone)
