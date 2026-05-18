from datetime import datetime, time

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.schemas.cafe import CafeShortInfo
from src.services.constants import DESCRIPTION_MAX_LENGHT, MIN_NUMBER


class TimeSlotCreate(BaseModel):
    """Создание временного слота."""

    cafe_id: int = Field(..., title="Cafe Id", ge=MIN_NUMBER)
    start_time: time = Field(..., title="Start Time")
    end_time: time = Field(..., title="End Time")
    description: str = Field(
        ...,
        title="Description",
        min_length=MIN_NUMBER,
        max_length=DESCRIPTION_MAX_LENGHT,
    )

    @field_validator("description", mode="before")
    @classmethod
    def description_strip(cls, value: object) -> object:
        """Удаление пробелов."""
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_times(self) -> "TimeSlotCreate":
        """Проверка времени."""
        if self.start_time >= self.end_time:
            raise ValueError("start_time должен быть меньше end_time")
        return self


class TimeSlotUpdate(BaseModel):
    """Обновление временного слота."""

    cafe_id: int | None = Field(None, title="Cafe Id", ge=MIN_NUMBER)
    start_time: time | None = Field(None, title="Start Time")
    end_time: time | None = Field(None, title="End Time")
    description: str | None = Field(
        None,
        title="Description",
        min_length=MIN_NUMBER,
        max_length=DESCRIPTION_MAX_LENGHT,
    )
    is_active: bool | None = Field(None, title="Is Active")

    @field_validator("description", mode="before")
    @classmethod
    def description_strip_optional(cls, value: object) -> object:
        """Удаление пробелов."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("description")
    @classmethod
    def description_no_blank_on_update(cls, value: str | None) -> str | None:
        """Проврека описания на пустоту."""
        if value is None:
            return None
        if not value:
            raise ValueError(
                "Описание не может быть пустым или из одних пробелов",
            )
        return value

    @model_validator(mode="after")
    def validate_times(self) -> "TimeSlotUpdate":
        """Проверяем корректность временных интервалов при обновлении.

        При условии передачи двух значений времени.
        """
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("start_time должен быть меньше end_time")
        return self


class TimeSlotInfo(BaseModel):
    """Ответ API: собирается из ORM-модели TimeSlot (from_attributes).

    Поле "cafe" формируется из "cafe_id" слота, без ручной сборки в роутере.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    cafe_id: int = Field(exclude=True)
    start_time: time
    end_time: time
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    cafe: CafeShortInfo


class TimeSlotShortInfo(BaseModel):
    """Краткая схема."""

    id: int
    start_time: time = Field(..., title="Start Time")
    end_time: time = Field(..., title="End Time")
    description: str = Field(
        ...,
        title="Description",
        min_length=MIN_NUMBER,
        max_length=DESCRIPTION_MAX_LENGHT,
    )
