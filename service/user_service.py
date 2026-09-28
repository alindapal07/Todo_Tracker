from datetime import UTC, datetime

from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    refresh_session,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    verify_password,
)
from errors.exceptions import InvalidCurrentPassword, UserAlreadyExists
from models.user_model import User
from repositories.user_repositories import UserRepository
from schemas.auth_schema import PasswordChangeRequest, UserLogin, UserRegister



class userService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self.repository.get_user_by_id(user_id)

    async def find_user_by_id(self, user_id: str) -> User | None:
        return await self.repository.get_user_by_id(user_id)

    async def find_user_by_username_or_email(self, identifier: str) -> User | None:
        return await self.repository.get_user_by_username_or_email(identifier)

    async def register_user(self, user_data: UserRegister) -> User:
        existing_username = await self.repository.get_user_by_username(user_data.username)
        if existing_username:
            raise UserAlreadyExists("Username already exists")

        existing_email = await self.repository.get_user_by_email(user_data.email)
        if existing_email:
            raise UserAlreadyExists("Email already exists")


        hashed_password = hash_password(user_data.password)
        display_name = user_data.name or user_data.username

        user = User(
            username=user_data.username,
            name=display_name,
            email=user_data.email,
            password_hash=hashed_password,
            is_active=True,
        )
        return await self.repository.create(user)

    async def login_user(
        self,
        login_data: UserLogin,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[dict[str, str], str]:
        user = await self.find_user_by_username_or_email(login_data.username)
        if user is None or not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid username or password")

        if not user.is_active:
            raise ValueError("Invalid username or password")

        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
        )

        raw_refresh_token, _ = await create_refresh_token(
            db=self.repository.db,
            user_id=user.id,
            ip_address=ip,
            user_agent=user_agent,
        )

        token_payload = {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "bearer",
        }
        return token_payload, raw_refresh_token

    async def refresh_session(
        self,
        raw_refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[dict[str, str], str]:
        return await refresh_session(
            db=self.repository.db,
            raw_refresh_token=raw_refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def refresh_token(
        self,
        raw_refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[dict[str, str], str]:
        return await self.refresh_session(
            raw_refresh_token=raw_refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def revoke_refresh_token(self, raw_refresh_token: str) -> None:
        await revoke_refresh_token(
            db=self.repository.db,
            raw_refresh_token=raw_refresh_token,
        )

    async def revoke_token(self, raw_refresh_token: str) -> None:
        await self.revoke_refresh_token(raw_refresh_token)

    async def change_password(
        self,
        user: User,
        data: PasswordChangeRequest,
    ) -> User:
        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCurrentPassword("Current password is incorrect")

        try:
            user.password_hash = hash_password(data.new_password)
            user.password_changed_at = datetime.now(UTC)

            await revoke_all_user_refresh_tokens(
                db=self.repository.db,
                user_id=user.id,
            )

            await self.repository.db.commit()
            await self.repository.db.refresh(user)
            return user
        except Exception:
            await self.repository.db.rollback()
            raise