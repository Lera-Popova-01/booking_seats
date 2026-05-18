import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from src.models.enums import UserRole
from src.services.constants import (
    MAX_LENGTH_PASSWORD,
    MIN_LENGTH_PASSWORD,
    MIN_LENGTH_USERNAME,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    TG_ID_MAX_LENGTH,
)
from src.services.phone_validation import validate_phone_number


class UserFiltersSchema(BaseModel):
    """Базовая схема с фильтрацией данных."""

    show_all: bool = Field(False, description='Включая удаленных')
    role: Optional[str] = Field(None, description='Фильтр по роли')

    model_config = {"extra": "forbid"}


class UserBase(BaseModel):
    """Базовая схема с общими полями."""

    username: str = Field(
        min_length=MIN_LENGTH_USERNAME, max_length=NAME_MAX_LENGTH,
    )
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=PHONE_MAX_LENGTH)
    tg_id: Optional[str] = Field(default=None, max_length=TG_ID_MAX_LENGTH)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, phone: Optional[str]) -> Optional[str]:
        """Валидация и нормализация номера телефона."""
        return validate_phone_number(phone)


class UserCreate(UserBase):
    """Создание нового пользователя."""

    password: str = Field(
        min_length=MIN_LENGTH_PASSWORD, max_length=MAX_LENGTH_PASSWORD,
    )
    role: Optional[UserRole] = Field(
        default=UserRole.USER,
        description='Роль пользователя (только для админов)',
    )

    @model_validator(mode='after')
    def validate_email_or_phone(self) -> 'UserCreate':
        """Проверить, что указан хотя бы один контактный идентификатор."""
        if not self.email and not self.phone:
            raise ValueError('Необходимо указать email или телефон')
        return self

    def create_update_dict_superuser(self) -> dict:
        """Создать словарь для обновления суперпользователем.

        Метод требуется для совместимости с FastAPI Users.
        """
        return self.model_dump(exclude_unset=True)


class UserUpdate(BaseModel):
    """Обновление пользователя администратором."""

    username: Optional[str] = Field(
        default=None,
        min_length=MIN_LENGTH_USERNAME,
        max_length=NAME_MAX_LENGTH,
    )
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=PHONE_MAX_LENGTH)
    tg_id: Optional[str] = Field(default=None, max_length=TG_ID_MAX_LENGTH)
    password: Optional[str] = Field(
        default=None,
        min_length=MIN_LENGTH_PASSWORD,
        max_length=MAX_LENGTH_PASSWORD,
    )
    role: Optional[UserRole] = None
    is_active: Optional[bool] = Field(
        default=None, description="Блокировка/разблокировка",
    )

    @field_validator('phone')
    @classmethod
    def validate_phone_number(cls, phone: Optional[str]) -> Optional[str]:
        """Валидация телефона при обновлении."""
        return validate_phone_number(phone)

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'UserUpdate':
        """Проверить, что хотя бы одно поле для обновления указано."""
        values = self.model_dump(exclude_unset=True)

        if not values:
            raise ValueError(
                'Должно быть указано хотя бы одно поле для обновления',
            )

        return self

    @model_validator(mode='after')
    def validate_email_format(self) -> 'UserUpdate':
        """Дополнительная проверка email (если передан)."""
        if self.email is not None and not isinstance(self.email, EmailStr):
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
                raise ValueError('Неверный формат email')
        return self


class UserSelfUpdate(BaseModel):
    """Обновление своего профиля (ограниченные поля)."""

    username: Optional[str] = Field(
        default=None,
        min_length=MIN_LENGTH_USERNAME,
        max_length=NAME_MAX_LENGTH,
    )
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=PHONE_MAX_LENGTH)
    tg_id: Optional[str] = Field(default=None, max_length=TG_ID_MAX_LENGTH)
    password: Optional[str] = Field(
        default=None,
        min_length=MIN_LENGTH_PASSWORD,
        max_length=MAX_LENGTH_PASSWORD,
    )

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, phone: Optional[str]) -> Optional[str]:
        """Валидация телефона при обновлении профиля."""
        return validate_phone_number(phone)

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'UserSelfUpdate':
        """Проверить, что хотя бы одно поле для обновления указано."""
        values = self.model_dump(exclude_unset=True)

        if not values:
            raise ValueError(
                'Должно быть указано хотя бы одно поле для обновления',
            )

        return self


class UserRead(UserBase):
    """Чтение данных пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    is_active: bool = Field(
        description="Пользователь активен (не заблокирован)",
    )
    created_at: datetime
    updated_at: datetime


class UserShortInfo(UserBase):
    """Краткая информация пользователя."""

    id: UUID
