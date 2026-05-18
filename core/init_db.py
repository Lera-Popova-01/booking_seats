import asyncio
import contextlib
import logging

from fastapi_users.exceptions import UserAlreadyExists

from src.core.config import settings
from src.core.db import get_async_session
from src.core.security import get_user_db, get_user_manager
from src.models.enums import UserRole
from src.schemas.user import UserCreate

logger = logging.getLogger(__name__)

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_superuser() -> None:
    """Создать суперпользователя."""
    if not settings.first_superuser_email or not (
        settings.first_superuser_password
    ):
        logger.warning("Настройки суперпользователя не указаны")
        return

    logger.info("Создание суперпользователя...")

    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=settings.first_superuser_email,
                            username=settings.first_superuser_username or (
                                "admin"
                            ),
                            phone=settings.first_superuser_phone,
                            password=settings.first_superuser_password,
                            role=UserRole.ADMIN,
                        ),
                    )
                    logger.info("=" * 50)
                    logger.info("Суперпользователь создан!")
                    logger.info(f"Email: {user.email}")
                    logger.info(f"Пароль: {settings.first_superuser_password}")
                    logger.info(f"Имя: {user.username}")
                    logger.info(f"Роль: {user.role}")
                    logger.info("=" * 50)
    except UserAlreadyExists:
        logger.info(
            f"Суперпользователь"
            f"{settings.first_superuser_email} уже существует",
        )
    except Exception as e:
        logger.error(f"Ошибка при создании суперпользователя: {e}")


if __name__ == "__main__":
    asyncio.run(create_superuser())
