from sqlalchemy import Column, ForeignKey, Integer, Table, Uuid

from src.core.db import Base

cafe_managers = Table(
    'cafe_managers',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafe.id'), primary_key=True),
    Column(
        'user_id', Uuid(
            as_uuid=True), ForeignKey('users.id'), primary_key=True,
    ),
)
