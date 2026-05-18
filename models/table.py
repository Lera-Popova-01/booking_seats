from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.db import Base
from src.services.constants import SEAT_GT, SEAT_LE


class Table(Base):
    """Модель столов в базе данных.

    Представляет стол в кафе с информацией о количестве мест и описанием.

    Attributes:
        seat_number (int): Количество мест за столом (обязательное поле).
        description (str): Краткое описание стола (обязательное поле).
        cafe_id (int): ID кафе, к которому относится стол (FK на таблицу Cafe).

        От Base:
        created_at (datetime): Дата и время создания записи в БД.
        updated_at (datetime): Дата и время обновления записи в БД.
        is_active (bool): активный объект или нет.

    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    cafe_id: Mapped[int] = mapped_column(ForeignKey('cafe.id'))
    cafe: Mapped['Cafe'] = relationship('Cafe')  # noqa: F821

    __table_args__ = (
        CheckConstraint('seat_number > 0', name='check_seat_number_positive'),
        CheckConstraint('seat_number <= 20', name='check_seat_number_max'),
        CheckConstraint(
            'length(trim(description)) > 0',
            name='check_description_not_empty',
        ),
    )

    @validates('seat_number')
    def validate_seat_number(self, key: str, value: int) -> int:
        """Проверяем количество мест."""
        if value <= SEAT_GT:
            raise ValueError('Количество мест должно быть больше 0')
        if value > SEAT_LE:
            raise ValueError('Слишком большое количество мест (макс. 20)')
        return value

    @validates('description')
    def validate_description(self, key: str, value: str) -> str:
        """Проверяем описание поля на пустоту."""
        if not value or not value.strip():
            raise ValueError('Описание не должно быть пустым')
        return value.strip()
