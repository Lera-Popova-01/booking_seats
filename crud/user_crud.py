from typing import Any, Dict, Optional, Set
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.base import CRUDBase
from src.models import User, UserRole
from src.schemas.user import UserCreate, UserUpdate
from src.users.manager import password_helper


class CRUDUser(CRUDBase):
    """CRUD операции для модели User."""

    _PROTECTED_FIELDS: Set[str] = {
        'id',
        'created_at',
        'updated_at',
        'hashed_password',
    }

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Получить пользователя по email."""
        query = select(self.model).where(self.model.email == email)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        session: AsyncSession,
        phone: str,
    ) -> Optional[User]:
        """Получить пользователя по телефону."""
        query = select(self.model).where(self.model.phone == phone)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email_or_phone(
        self,
        session: AsyncSession,
        email: Optional[str],
        phone: Optional[str],
    ) -> Optional[User]:
        """Получить пользователя по email ИЛИ phone."""
        conditions = []
        if email:
            conditions.append(self.model.email == email)
        if phone:
            conditions.append(self.model.phone == phone)

        if not conditions:
            return None

        query = select(self.model).where(or_(*conditions))
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _build_conditions(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        exclude_id: Optional[UUID] = None,
    ) -> tuple[list, Optional[UUID]]:
        """Построить условия для поиска."""
        conditions = []
        if email:
            conditions.append(self.model.email == email)
        if phone:
            conditions.append(self.model.phone == phone)
        return conditions, exclude_id

    async def check_exists(
        self,
        session: AsyncSession,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Проверить существование пользователя.

        Возвращает True, если пользователь существует, иначе False.
        """
        conditions, exclude_id = await self._build_conditions(
            email,
            phone,
            exclude_id,
        )

        if not conditions:
            return False

        query = select(func.exists().where(or_(*conditions)))
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await session.execute(query)
        return result.scalar() or False

    async def create_with_role(
        self,
        session: AsyncSession,
        obj_in: UserCreate,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Создать пользователя с указанной ролью."""
        obj_in_data = obj_in.model_dump()
        obj_in_data['hashed_password'] = password_helper.hash(
            obj_in_data.pop('password'),
        )
        obj_in_data['role'] = role
        obj_in_data['is_active'] = True
        obj_in_data['is_verified'] = True

        if 'email' in obj_in_data and obj_in_data['email'] is None:
            pass

        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        return db_obj

    async def update_user(
        self,
        session: AsyncSession,
        db_obj: User,
        obj_in: UserUpdate,
    ) -> User:
        """Обновить пользователя."""
        update_data = obj_in.model_dump(exclude_unset=True)

        if 'password' in update_data:
            password = update_data.pop('password')
            update_data['hashed_password'] = password_helper.hash(password)

        update_data = self._filter_protected_fields(update_data)

        return await self.update(
            session=session, db_obj=db_obj, update_data=update_data,
        )

    def _filter_protected_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Исключить защищённые поля из данных для обновления.

        Args:
            data: Словарь с данными для обновления

        Returns:
            Dict[str, Any]: Очищенный словарь без защищённых полей

        """
        return {
            key: value
            for key, value in data.items()
            if key not in self._PROTECTED_FIELDS
        }

    async def block(
        self,
        session: AsyncSession,
        db_obj: User,
    ) -> User:
        """Заблокировать пользователя."""
        return await self.update(
            session=session, db_obj=db_obj, update_data={'is_active': False},
        )

    async def unblock(
        self,
        session: AsyncSession,
        db_obj: User,
    ) -> User:
        """Разблокировать пользователя."""
        return await self.update(
            session=session, db_obj=db_obj, update_data={'is_active': True},
        )

    async def count(
        self,
        session: AsyncSession,
        role: Optional[str] = None,
        include_inactive: bool = False,
    ) -> int:
        """Подсчитать количество пользователей."""
        filters = {}
        if role:
            filters['role'] = role

        show_active = None if include_inactive else True
        return await self.get_count(
            session, show_active=show_active, **filters,
        )


user_crud = CRUDUser(User)
