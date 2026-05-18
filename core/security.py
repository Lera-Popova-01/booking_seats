from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_async_session
from src.models import User, UserRole
from src.users.manager import get_user_manager

STAFF_ROLES = {UserRole.MANAGER, UserRole.ADMIN}
ADMIN_ROLE = UserRole.ADMIN


bearer_transport = BearerTransport(tokenUrl='/auth/login')

security = HTTPBearer()


async def get_user_db(
        session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """Зависимость для получения базы данных пользователей."""
    yield SQLAlchemyUserDatabase(session, User)


def get_jwt_strategy() -> JWTStrategy:
    """Стратегия для JWT токенов."""
    return JWTStrategy(
        secret=settings.secret_key_str(),
        lifetime_seconds=settings.access_token_expire_minutes * 60,
        token_audience=['fastapi-users:auth'],
    )


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)


current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(active=True)
current_active_user_optional = fastapi_users.current_user(
    optional=True,
    active=True,
)


async def current_manager_user(
    user: User = Depends(current_active_user),
) -> User:
    """Зависимость, что пользователь является менеджером или админом."""
    if user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав.',
        )
    return user


async def current_admin_user(
    user: User = Depends(current_active_user),
) -> User:
    """Зависимость для проверки, что пользователь является администратором."""
    if user.role != ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав. Требуется роль администратора.',
        )
    return user


async def current_admin_user_optional(
    user: User | None = Depends(current_active_user_optional),
) -> User | None:
    """Опциональная зависимость администратора.

    Возвращает пользователя только если он авторизован и имеет роль admin.
    В остальных случаях возвращает None без ошибки.
    """
    if user is None or user.role != ADMIN_ROLE:
        return None
    return user


async def get_token_from_request(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Получить токен из заголовка Authorization."""
    return credentials.credentials


async def get_current_user_with_token(
    user: User = Depends(current_active_user),
    token: str = Depends(get_token_from_request),
) -> tuple[User, str]:
    """Получить текущего пользователя и его токен.

    Использовать когда нужно работать и с пользователем и с токеном.
    """
    return user, token


async def verify_token(
    token: str = Depends(get_token_from_request),
) -> dict:
    """Проверить валидность токена и вернуть его содержимое."""
    try:
        strategy = get_jwt_strategy()
        user_id = await strategy.read_token(token)

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Невалидный токен',
            )

        return {'valid': True, 'user_id': str(user_id)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Ошибка валидации токена: {str(e)}',
        )


async def current_staff_user(
    user: User = Depends(current_active_user),
) -> User:
    """Зависимость для проверки, что пользователь является персоналом."""
    if user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав. Требуется роль менеджера или админа.',
        )
    return user
