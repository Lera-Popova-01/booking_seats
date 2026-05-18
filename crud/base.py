import logging
from typing import Any, Optional, Sequence, Union
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.core.logging_setup import redact_sensitive_data

logger = logging.getLogger(__name__)


class CRUDBase:
    """Базовый класс CRUD."""

    def __init__(self, model: Any) -> None:
        """Инициализация объекта."""
        self.model = model
        self.model_atributes = {
            column.name for column in model.__table__.columns
        }

    def _filter_model_atributes(self, data: dict) -> dict:
        """Получение из словаря поля, которые принадлежат модели."""
        return {key: value for key, value in data.items()
                if key in self.model_atributes}

    def _apply_filters(
        self,
        query: Select,
        show_active: Optional[bool] = None,
        **filters: Any,
    ) -> Select:
        """Применение фильтров к запросу."""
        if show_active is not None:
            query = query.where(self.model.is_active == show_active)

        for field, value in filters.items():
            if value is None:
                continue
            if hasattr(self.model, field):
                if isinstance(value, list):
                    query = query.where(getattr(self.model, field).in_(value))
                else:
                    query = query.where(getattr(self.model, field) == value)

        return query

    async def get_by_id(
            self,
            obj_in: Union[int, UUID],
            session: AsyncSession,
            show_active: Optional[bool] = None,
            **filters: Any,
    ) -> Any | None:
        """Получение одного объекта из БД по id с фильтрацией."""
        query = select(self.model).where(self.model.id == obj_in)
        query = self._apply_filters(query, show_active, **filters)
        result = await session.execute(query)
        return result.scalars().first()

    async def get_multi(
            self,
            session: AsyncSession,
            show_active: Optional[bool] = None,
            **filters: Any,
    ) -> Sequence[Any]:
        """Получение всех объктов из БД."""
        query = select(self.model)
        query = self._apply_filters(query, show_active, **filters)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_count(
            self,
            session: AsyncSession,
            show_active: Optional[bool] = None,
            **filters: Any,
    ) -> int:
        """Получение количества объектов в БД."""
        query = select(func.count(self.model.id))
        query = self._apply_filters(query, show_active, **filters)
        result = await session.execute(query)
        return result.scalar() or 0

    async def create(
        self,
        object_in: Any,
        session: AsyncSession,
    ) -> Any:
        """Создание объекта."""
        object_in_data = object_in.model_dump()
        filter_data = self._filter_model_atributes(object_in_data)
        db_object = self.model(**filter_data)
        session.add(db_object)
        await session.commit()
        await session.refresh(db_object)
        logger.info(
            "Created %s id=%s payload=%s",
            self.model.__name__,
            getattr(db_object, "id", None),
            redact_sensitive_data(filter_data),
        )
        return db_object

    async def update(
        self,
        db_obj: Any,
        update_data: dict,
        session: AsyncSession,
    ) -> Any:
        """Изменение объекта."""
        filter_update_data = self._filter_model_atributes(update_data)

        for field in filter_update_data:
            setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        logger.info(
            "Updated %s id=%s changed_fields=%s payload=%s",
            self.model.__name__,
            getattr(db_obj, "id", None),
            sorted(filter_update_data.keys()),
            redact_sensitive_data(filter_update_data),
        )
        return db_obj
