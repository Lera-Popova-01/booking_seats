from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaInfo(BaseModel):
    """Схема для ответа после загрузки изображения."""

    media_id: UUID

    model_config = ConfigDict(extra='forbid')
