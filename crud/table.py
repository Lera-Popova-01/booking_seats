from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.crud.base import CRUDBase
from src.models import Table


class CRUDTable(CRUDBase):
    """Класс дополнительных методов модели Table."""

    async def create_with_cafe(
        self,
        object_in: Any,
        session: AsyncSession,
    ) -> Table:
        """Создать стол и вернуть с загрузкой кафе."""
        object_in_data = object_in.model_dump()
        filter_data = self._filter_model_atributes(object_in_data)
        db_object = self.model(**filter_data)
        session.add(db_object)
        await session.flush()
        result = await session.execute(
            select(self.model)
            .where(self.model.id == db_object.id)
            .options(selectinload(self.model.cafe)),
        )

        return result.scalars().first()

    async def get_by_id(
        self,
        obj_in: int,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        **filters: Any,
    ) -> Table:
        """Получение стола по id."""
        query = (
            select(Table)
            .options(selectinload(Table.cafe))
            .where(Table.id == obj_in)
        )

        query = self._apply_filters(query, show_active, **filters)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        **filters: Any,
    ) -> list[Any]:
        """Получение списка столов."""
        query = select(self.model)

        if hasattr(self.model, "cafe"):
            query = query.options(selectinload(self.model.cafe))

        query = self._apply_filters(query, show_active, **filters)

        result = await session.execute(query)
        return result.scalars().all()


table_crud = CRUDTable(Table)
