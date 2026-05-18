import logging
from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Request
from fastapi.responses import Response
from fastapi_users import BaseUserManager, UUIDIDMixin, exceptions, schemas
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_async_session
from src.models.user import User

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

password_helper = PasswordHelper()

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля."""
    return pwd_context.hash(password)


async def validate_password_strength(
        password: str, user_role: str = 'user',
) -> None:
    """Валидация сложности пароля с учетом роли пользователя."""
    min_length = 10 if user_role == 'admin' else 8

    if len(password) < min_length:
        raise ValueError(
            f'Пароль должен содержать минимум {min_length} символов',
        )

    if password.isdigit():
        raise ValueError('Пароль не может состоять только из цифр')

    if password.isalpha():
        raise ValueError('Пароль должен содержать хотя бы одну цифру')

    if user_role in ['manager', 'admin']:
        if not any(c.isupper() for c in password):
            raise ValueError(
                'Менеджер и администратор должны использовать заглавные буквы',
                )

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValueError(
                'Менеджеры и администраторы должны использовать спецсимволы',
            )


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """Менеджер пользователей для FastAPI Users."""

    reset_password_token_secret = settings.secret_key_str
    verification_token_secret = settings.secret_key_str

    reset_password_token_lifetime_seconds = 3600
    verification_token_lifetime_seconds = 3600

    async def validate_password(
        self,
        password: str,
        user: User | schemas.UC,
    ) -> None:
        """Валидация пароля при создании/изменении."""
        role = 'user'
        if isinstance(user, User):
            role = user.role

        try:
            await validate_password_strength(password, role)
        except ValueError as e:
            raise exceptions.InvalidPasswordException(str(e))

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """Действия после регистрации пользователя."""
        identifier = user.email or user.phone or user.username
        logger.info(f'Новый пользователь: {identifier} (ID: {user.id})')

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        """Действия после запроса сброса пароля."""
        if not user.email:
            logger.warning(
                f'Сброс пароля для пользователя без email: {user.id}',
            )
            return

        reset_url = f'/reset-password?token={token}'
        logger.info(f'Сброс пароля для {user.email}: {reset_url}')

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        """Действия после запроса верификации email."""
        if not user.email:
            logger.warning(
                f'Подтверждение пользователя без электронной почты: {user.id}',
            )
            return

        verify_url = f'/verify?token={token}'
        logger.info(f'Верификация email для {user.email}: {verify_url}')

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        """Действия после успешного входа."""
        identifier = user.email or user.phone
        logger.info(f'Успешный вход: {identifier} (ID: {user.id})')

    async def on_after_update(
        self,
        user: User,
        update_dict: dict,
        request: Optional[Request] = None,
    ) -> None:
        """Действия после обновления пользователя."""
        identifier = user.email or user.phone
        logger.info(
            f'Обновлен пользователь: {identifier} (ID: {user.id}) - '
            f'Fields: {list(update_dict.keys())}',
        )

    async def on_before_delete(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """Действия перед удалением пользователя."""
        identifier = user.email or user.phone
        logger.info(f'Удаление пользователя: {identifier} (ID: {user.id})')

    async def get_by_email(self, user_email: str) -> User:
        """Получить пользователя по email."""
        if not user_email:
            raise exceptions.UserNotExists()

        try:
            user = await super().get_by_email(user_email)
        except exceptions.UserNotExists:
            raise
        return user


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """Зависимость для получения базы данных пользователей."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Зависимость для получения менеджера пользователей."""
    yield UserManager(user_db)
