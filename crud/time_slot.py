from collections.abc import Sequence
from datetime import time

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.crud.base import CRUDBase
from src.models import TimeSlot


class CRUDTimeSlot(CRUDBase):
    """CRUD для временных слотов."""

    async def get_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
        *,
        show_all: bool = False,
    ) -> Sequence[TimeSlot]:
        """Получаем список слотов по ID кафе."""
        stmt = (
            select(TimeSlot)
            .where(TimeSlot.cafe_id == cafe_id)
            .options(selectinload(TimeSlot.cafe))
        )
        if not show_all:
            stmt = stmt.where(TimeSlot.is_active.is_(True))
        stmt = stmt.order_by(TimeSlot.start_time)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_id_in_cafe(
        self,
        cafe_id: int,
        slot_id: int,
        session: AsyncSession,
    ) -> TimeSlot | None:
        """Получить слот по ID в конкретном кафе."""
        result = await session.execute(
            select(TimeSlot)
            .options(selectinload(TimeSlot.cafe))
            .where(
                and_(
                    TimeSlot.id == slot_id,
                    TimeSlot.cafe_id == cafe_id,
                ),
            ),
        )
        return result.scalars().first()

    async def get_active_by_ids_in_cafe(
        self,
        session: AsyncSession,
        slots_id: list[int],
        cafe_id: int,
    ) -> Sequence[TimeSlot]:
        """Получить активные слоты по списку ID в конкретном кафе."""
        result = await session.execute(
            select(TimeSlot).where(
                TimeSlot.id.in_(slots_id),
                TimeSlot.cafe_id == cafe_id,
                TimeSlot.is_active.is_(True),
            ),
        )
        return result.scalars().all()

    async def find_active_time_overlap(
        self,
        session: AsyncSession,
        cafe_id: int,
        start_time: time,
        end_time: time,
        *,
        exclude_slot_id: int | None = None,
    ) -> TimeSlot | None:
        """Найти активный слот того же кафе.

        Чей интервал пересекается с [start, end).

        Граница не считается пересечением:
        [10:00, 12:00) и [12:00, 14:00) не конфликтуют.
        Полное совпадение интервалов — пересечение.
        """
        stmt = select(TimeSlot).where(
            TimeSlot.cafe_id == cafe_id,
            TimeSlot.is_active.is_(True),
            TimeSlot.start_time < end_time,
            TimeSlot.end_time > start_time,
        )
        if exclude_slot_id is not None:
            stmt = stmt.where(TimeSlot.id != exclude_slot_id)
        stmt = stmt.limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()


time_slot_crud = CRUDTimeSlot(TimeSlot)
