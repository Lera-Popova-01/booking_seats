import re
from typing import Annotated

from fastapi import Form
from pydantic import BaseModel


class OAuth2PasswordRequestFormCustom:
    """Кастомная форма для OAuth2 с минимальными полями."""

    def __init__(
        self,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ) -> None:
        """Инициализация формы аутентификации."""
        self.username = username
        self.password = password
        self._validate_username()

    def is_email(self) -> bool:
        """Проверить, является ли username email."""
        return '@' in self.username and '.' in self.username.split('@')[-1]

    def is_phone(self) -> bool:
        """Проверить, является ли username телефоном."""
        cleaned = re.sub(r'[\s\-\(\)]', '', self.username)
        return re.match(r'^\+?[0-9]{10,15}$', cleaned) is not None

    def _validate_username(self) -> None:
        """Проверить, что указан корректный идентификатор."""
        if not self.is_email() and not self.is_phone():
            raise ValueError('Необходимо передать email или телефон')


class TokenResponse(BaseModel):
    """Схема ответа с токеном доступа."""

    access_token: str
    token_type: str = 'bearer'
