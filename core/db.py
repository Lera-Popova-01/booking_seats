import logging
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

from src.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Базовый класс моделей.

    Добавляет имя класса, id, created_at, updated_at, active.
    """

    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        """Автоматическое имя таблицы."""
        return cls.__name__.lower()

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )


engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Получение сессии БД."""
    async with AsyncSessionLocal() as async_session:
        try:
            logger.debug("Creating database session")
            yield async_session
            logger.debug("Database session closed successfully")
        except SQLAlchemyError:
            logger.error(
                "Database error: %s",
                str(SQLAlchemyError),
                exc_info=True,
            )
            await async_session.rollback()
            raise
