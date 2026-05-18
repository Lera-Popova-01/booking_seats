from uuid import UUID

from sqlalchemy import (
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.associations import cafe_managers
from src.models.user import User
from src.services.constants import (
    ADDRESS_MAX_LENGTH,
    DESCRIPTION_MAX_LENGHT,
    NAME_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)


class Cafe(Base):
    """Модель кафе."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), unique=True)
    address: Mapped[str] = mapped_column(
        String(ADDRESS_MAX_LENGTH), nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(PHONE_MAX_LENGTH), nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(DESCRIPTION_MAX_LENGHT), nullable=False,
    )
    photo: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )

    managers: Mapped[list['User']] = relationship(
        'User',
        secondary=cafe_managers,
        lazy="selectin",
        back_populates="cafes",
    )

    __table_args__ = (
        UniqueConstraint('name', 'address', name='unique_name_address'),
    )
