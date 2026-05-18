from uuid import UUID, uuid4

from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.services.constants import CONTENT_TYPE_MAX_LENGTH, NAME_MAX_LENGTH


class Media(Base):
    """Изображения."""

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, unique=True, nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    content_type: Mapped[str] = mapped_column(
        String(CONTENT_TYPE_MAX_LENGTH), nullable=False,
    )
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
