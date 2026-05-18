from typing import TYPE_CHECKING, Optional

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.associations import cafe_managers
from src.models.enums import UserRole
from src.services.constants import (
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
    ROLE_MAX_LENGTH,
    TG_ID_MAX_LENGTH,
)

if TYPE_CHECKING:
    from src.models.cafe import Cafe


class User(Base, SQLAlchemyBaseUserTableUUID):
    """Модель пользователя."""

    __tablename__ = 'users'

    email: Mapped[Optional[str]] = mapped_column(
        String(length=320),
        unique=True,
        index=True,
        nullable=True,
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(PHONE_MAX_LENGTH),
        unique=True,
        nullable=True,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(NAME_MAX_LENGTH), nullable=False,
    )

    tg_id: Mapped[Optional[str]] = mapped_column(
        String(TG_ID_MAX_LENGTH), nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(ROLE_MAX_LENGTH),
        default=UserRole.USER,
        nullable=False,
    )

    cafes: Mapped[list['Cafe']] = relationship(
        'Cafe',
        secondary=cafe_managers,
        back_populates='managers',
        lazy="selectin",
    )
