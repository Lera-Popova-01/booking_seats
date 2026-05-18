from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.base import CRUDBase
from src.models import Media


class CRUDMedia(CRUDBase):
    """CRUD для изображений."""

    async def get_image_by_id(
            self,
            media_id: UUID,
            session: AsyncSession,
            show_active: Optional[bool] = None,
    ) -> Optional[Media]:
        """Получени медиа по id с фильтрацией по активности."""
        query = select(Media).where(Media.id == media_id)
        if show_active is not None:
            query = query.where(Media.is_active == show_active)
        media = await session.execute(query)
        return media.scalars().first()

    async def create_from_bytes(
            self,
            file_data: bytes,
            filename: str,
            content_type: str,
            session: AsyncSession,
    ) -> Media:
        """Создание медиа из байтов."""
        media = Media(
            data=file_data,
            filename=filename,
            content_type=content_type,
            size=len(file_data),
        )
        session.add(media)
        await session.commit()
        await session.refresh(media)
        return media


media_crud = CRUDMedia(Media)
