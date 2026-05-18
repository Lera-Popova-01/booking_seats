from pydantic import BaseModel


class CustomError(BaseModel):
    """Схема для кастомных ошибок."""

    code: int
    message: str
