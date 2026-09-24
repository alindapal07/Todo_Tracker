from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: str) -> User | None:
        statement = select(User).where(User.id == str(user_id))
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, user_email: str) -> User | None:
        statement = select(User).where(func.lower(User.email) == user_email.strip().lower())
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        statement = select(User).where(func.lower(User.username) == username.strip().lower())
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_username_or_email(self, identifier: str) -> User | None:
        clean_identifier = identifier.strip().lower()
        statement = select(User).where(
            or_(
                func.lower(User.username) == clean_identifier,
                func.lower(User.email) == clean_identifier,
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_user(self) -> list[User]:
        statement = select(User)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.commit()