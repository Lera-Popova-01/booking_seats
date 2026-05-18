from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.crud.base import CRUDBase
from src.models import Cafe, User, UserRole


class CRUDCafe(CRUDBase):
    """CRUD для кафе."""

    async def _validate_managers(
            self,
            managers_id: list[UUID],
            session: AsyncSession,
            exclude_cafe_id: Optional[int] = None,
    ) -> list[User]:
        """Валидация менеджеров."""
        if not managers_id:
            raise ValueError(
                'Добавьте хотя бы одного менеджера',
            )
        result = await session.execute(
            select(User).where(User.id.in_(managers_id)),
        )
        managers = result.scalars().all()
        missing_ids = [
            str(m_id) for m_id in managers_id if str(m_id) not in {
                str(manager.id) for manager in managers
            }
        ]
        if missing_ids:
            raise ValueError(
                f'Пользователи с ID {", ".join(missing_ids)} не найдены')
        for manager in managers:
            if manager.role not in (UserRole.MANAGER, UserRole.ADMIN):
                raise ValueError(
                    f'Пользователь {manager.id} '
                    'не является менеджером или администратором',
                )
            if manager.role == UserRole.MANAGER:
                existing_cafes = [
                    cafe.id for cafe in manager.cafes
                    if cafe.id != exclude_cafe_id
                ]
                if existing_cafes:
                    raise ValueError(
                        f'Менеджер {manager.id} '
                        'уже является менеджером кафе с  id: {existing_cafes}',
                    )
        return managers

    async def get_cafe_id_by_name(
            self,
            cafe_name: str,
            session: AsyncSession,
    ) -> Optional[int]:
        """Получение названия кафе по id."""
        cafe_id = await session.execute(
            select(Cafe.id).where(
                Cafe.name == cafe_name,
            ),
        )
        return cafe_id.scalars().first()

    async def get_by_id_with_managers(
        self,
        cafe_id: int,
        session: AsyncSession,
    ) -> Optional[Cafe]:
        """Получить кафе по ID с загрузкой менеджеров."""
        result = await session.execute(
            select(Cafe).where(
                Cafe.id == cafe_id,
            ).options(selectinload(Cafe.managers)),
        )
        return result.scalar_one_or_none()

    async def get_cafe_with_access_check(
        self,
        cafe_id: int,
        user: User,
        session: AsyncSession,
    ) -> Optional[Cafe]:
        """Получить кафе, если пользователь имеет к нему доступ."""
        cafe = await self.get_by_id_with_managers(cafe_id, session)
        if not cafe:
            return None
        if user.role == UserRole.ADMIN:
            return cafe
        if user.id in [manager.id for manager in cafe.managers]:
            return cafe
        return None

    async def create_with_managers(
        self,
        cafe_data: dict,
        managers_id: list[UUID],
        session: AsyncSession,
    ) -> Cafe:
        """Создать кафе и вернуть с загруженными менеджерами."""
        managers = await self._validate_managers(managers_id, session)
        cafe = self.model(**cafe_data)
        session.add(cafe)
        await session.flush()
        cafe_with_managers = await session.execute(
            select(Cafe).where(
                Cafe.id == cafe.id,
            ).options(selectinload(Cafe.managers)),
        )
        cafe = cafe_with_managers.scalar_one()
        cafe.managers = managers
        await session.commit()
        await session.refresh(cafe)
        return await self.get_by_id_with_managers(cafe.id, session)

    async def replace_cafe_managers(
        self,
        cafe_id: int,
        managers_id: list[UUID],
        session: AsyncSession,
        current_user: User,
    ) -> None:
        """Полностью заменить список менеджеров кафе."""
        cafe = await self.get_by_id_with_managers(cafe_id, session)
        if not cafe:
            raise ValueError(f'Кафе с: {cafe_id} не найдено')
        is_admin = current_user.role == UserRole.ADMIN
        is_manager_of_cafe = current_user in cafe.managers
        if not (is_admin or is_manager_of_cafe):
            raise ValueError('У вас нет доступа к этому кафе')
        new_managers = await self._validate_managers(
            managers_id, session, cafe_id,
        )
        cafe.managers = new_managers
        await session.commit()

    async def update_cafe_with_check(
        self,
        cafe_id: int,
        update_data: dict,
        user: User,
        session: AsyncSession,
    ) -> Optional[Cafe]:
        """Обновить кафе с проверкой прав."""
        cafe = await self.get_cafe_with_access_check(cafe_id, user, session)
        if not cafe:
            return None
        for field, value in update_data.items():
            if hasattr(cafe, field):
                setattr(cafe, field, value)
        await session.commit()
        await session.refresh(cafe)
        return cafe

    async def get_cafe_by_name_address(
            self,
            cafe_name: str,
            cafe_address: str,
            session: AsyncSession,
            exclude_id: Optional[int] = None,
    ) -> Optional[Cafe]:
        """Получение кафе по имени и адресу."""
        query = select(self.model).where(
            Cafe.name == cafe_name,
            Cafe.address == cafe_address,
        )
        if exclude_id is not None:
            query = query.where(self.model.id != exclude_id)
        result = await session.execute(query)
        return result.scalars().first()


cafe_crud = CRUDCafe(Cafe)
