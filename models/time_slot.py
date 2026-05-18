from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.db import Base
from src.services.constants import DESCRIPTION_MAX_LENGHT


class TimeSlot(Base):
    """Модель временного слота для бронирования столов."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Храним связь по id, но не накладываем внешний ключ,
    # чтобы ветка "слоты" не зависела от реализации модели "кафе".
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey('cafe.id'),
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    description: Mapped[str] = mapped_column(
        String(DESCRIPTION_MAX_LENGHT), nullable=False,
    )
    cafe: Mapped['Cafe'] = relationship('Cafe')  # noqa: F821

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="check_time_slot_times"),
        CheckConstraint(
            "cafe_id > 0",
            name="check_time_slot_cafe_id_positive",
        ),
        # Непустое описание (дублирует правила Pydantic на уровне БД;
        # length — PostgreSQL/SQLite).
        CheckConstraint(
            "length(description) >= 1",
            name="check_time_slot_description_min_len",
        ),
    )

    @validates("description")
    def _validate_description(self, _key: str, value: str) -> str:
        text = (value or "").strip()
        if not text:
            raise ValueError("Описание не может быть пустым")
        if len(text) > 1024:
            raise ValueError("Описание не длиннее 1024 символов")
        return text
