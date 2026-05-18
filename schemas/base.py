from datetime import datetime

from pydantic import BaseModel


class BaseShema(BaseModel):
    """Базовая схема (добавляет is_active, created_at, updated_at)."""

    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
