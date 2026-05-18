from typing import Annotated, Optional

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_session
from src.core.security import (
    current_active_user,
    current_admin_user,
    current_admin_user_optional,
    current_manager_user,
    current_staff_user,
)
from src.models.user import User
from src.schemas.user import UserFiltersSchema
from src.services.constants import DEFAULT_LIMIT, MAX_LIMIT, MIN_NUMBER, SKIP

DatabaseSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUser = Annotated[User, Depends(current_active_user)]
CurrentAdmin = Annotated[User, Depends(current_admin_user)]
OptionalCurrentAdmin = Annotated[
    User | None, Depends(current_admin_user_optional),
]
CurrentManager = Annotated[User, Depends(current_manager_user)]
CurrentStaff = Annotated[User, Depends(current_staff_user)]


def pagination_params(
    skip: int = Query(SKIP, ge=SKIP, description='Сколько записей пропустить'),
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=MIN_NUMBER,
        le=MAX_LIMIT,
        description='Сколько записей вернуть',
    ),
) -> tuple[int, int]:
    """Параметры пагинации для эндпоинтов со списками."""
    return skip, limit


Pagination = Annotated[tuple[int, int], Depends(pagination_params)]


def user_filters(
    show_all: bool = Query(False, description='Включая удаленных'),
    role: Optional[str] = Query(None, description='Фильтр по роли'),
) -> UserFiltersSchema:
    """Параметры фильтрации для списка пользователей."""
    return UserFiltersSchema(show_all=show_all, role=role)


UserFilters = Annotated[UserFiltersSchema, Depends(user_filters)]
