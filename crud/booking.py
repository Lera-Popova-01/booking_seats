import logging
from typing import Any, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from src.crud.base import CRUDBase
from src.models import Booking, BookingStatus, Table, TimeSlot
from src.models.booking import booking_tables_slots

logger = logging.getLogger(__name__)


class CRUDBooking(CRUDBase):
    """CRUD для операций с бронированиями."""

    async def get_with_relations(
        self,
        booking_id: int,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[Booking]:
        """Получаем конкретное бронирование."""
        query = select(self.model).where(self.model.id == booking_id).options(
            selectinload(self.model.user),
            selectinload(self.model.cafe),
            selectinload(self.model.tables),
            selectinload(self.model.slots),
        )
        query = self._apply_filters(query, show_active)
        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        **filters: Any,
    ) -> Sequence[Booking]:
        """Получаем все объекты со связанными данными."""
        query = select(self.model).options(
            selectinload(self.model.user),
            selectinload(self.model.cafe),
            selectinload(self.model.tables),
            selectinload(self.model.slots),
        )
        query = self._apply_filters(query, show_active, **filters)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        user_id: Optional[UUID] = None,
    ) -> Sequence[Booking]:
        """Получаем бронирования по кафе."""
        query = select(self.model).where(self.model.cafe_id == cafe_id)
        query = query.options(
            selectinload(self.model.user),
            selectinload(self.model.cafe),
            selectinload(self.model.tables),
            selectinload(self.model.slots),
        )
        query = self._apply_filters(query, show_active)

        if user_id is not None:
            query = query.where(self.model.user_id == user_id)

        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_manager_cafes(
        self,
        manager_cafe_ids: List[int],
        session: AsyncSession,
        show_active: Optional[bool] = None,
        user_id: Optional[UUID] = None,
    ) -> Sequence[Booking]:
        """Получение бронирований для менеджера по его кафе."""
        if not manager_cafe_ids:
            return []
        query = select(self.model).where(
            self.model.cafe_id.in_(manager_cafe_ids),
        )
        query = query.options(
            selectinload(self.model.user),
            selectinload(self.model.cafe),
            selectinload(self.model.tables),
            selectinload(self.model.slots),
        )
        query = self._apply_filters(query, show_active)

        if user_id is not None:
            query = query.where(self.model.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_user(
        self,
        user_id: UUID,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        cafe_id: Optional[int] = None,
    ) -> Sequence[Booking]:
        """Получаем бронирование пользователя."""
        query = select(self.model).where(self.model.user_id == user_id)
        query = query.options(
            selectinload(self.model.user),
            selectinload(self.model.cafe),
            selectinload(self.model.tables),
            selectinload(self.model.slots),
        )
        query = self._apply_filters(query, show_active)

        if cafe_id is not None:
            query = query.where(self.model.cafe_id == cafe_id)

        result = await session.execute(query)
        return result.scalars().all()

    async def create_with_relations(
        self,
        obj_in: Any,
        session: AsyncSession,
        user_id: UUID,
        tables: List[Table],
        slots: List[TimeSlot],
    ) -> Booking:
        """Создание бронирования."""
        booking_data = obj_in.model_dump(exclude={'tables_id', 'slots_id'})
        booking_data['user_id'] = user_id
        booking_data['status'] = BookingStatus.BOOKING.value
        filter_data = self._filter_model_atributes(booking_data)
        db_booking = self.model(**filter_data)

        session.add(db_booking)
        await session.flush()

        for table in tables:
            for slot in slots:
                await session.execute(
                    booking_tables_slots.insert().values(
                        booking_id=db_booking.id,
                        table_id=table.id,
                        slot_id=slot.id,
                        booking_date=db_booking.booking_date,
                    ),
                )

        logger.info(
            "Booking created: booking_id=%s user_id=%s cafe_id=%s date=%s",
            db_booking.id,
            user_id,
            db_booking.cafe_id,
            db_booking.booking_date,
        )
        return db_booking

    async def update_with_relations(
        self,
        db_booking: Booking,
        obj_in: Any,
        session: AsyncSession,
        tables: Optional[List[Table]] = None,
        slots: Optional[List[TimeSlot]] = None,
    ) -> Booking:
        """Обновляем бронирование."""
        update_data = obj_in.model_dump(exclude_unset=True)
        update_data = {
            k: v for k, v in update_data.items()
            if k in self.model_atributes and v is not None
        }
        for field, value in update_data.items():
            setattr(db_booking, field, value)

        def update_relations(sync_session: Session) -> None:
            """Обновляем отношения в синхронном контексте."""
            if tables is not None:
                db_booking.tables = tables
            if slots is not None:
                db_booking.slots = slots
            sync_session.add(db_booking)

        await session.run_sync(update_relations)
        logger.info(
            "Booking updated: booking_id=%s updated_fields=%s",
            db_booking.id,
            list(update_data.keys()),
        )
        return db_booking


booking_crud = CRUDBooking(Booking)
