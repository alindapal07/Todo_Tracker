from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from errors.exceptions import InvalidCurrentPassword, UserAlreadyExists
from models.refreshToken_model import RefreshToken
from models.user_model import User
from repositories.user_repositories import UserRepository
from schemas.auth_schema import PasswordChangeRequest, UserLogin, UserRegister


class userService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_id(self, user_id: str) -> User | None:
        # find user by user id
        return await self.repository.get_user_by_id(user_id)

    async def find_user_by_id(self, user_id: str) -> User | None:
        # alias helper to find user by id
        return await self.repository.get_user_by_id(user_id)

    async def find_user_by_username_or_email(self, identifier: str) -> User | None:
        # helper to search user using either username or email
        return await self.repository.get_user_by_username_or_email(identifier)

    async def register_user(self, user_data: UserRegister) -> User:
        # check if someone already took this username
        existing_username = await self.repository.get_user_by_username(
            user_data.username
        )
        if existing_username:
            raise UserAlreadyExists("Username already exists")

        # check if this email is already registered
        existing_email = await self.repository.get_user_by_email(user_data.email)
        if existing_email:
            raise UserAlreadyExists("Email already exists")

        # hash password before storing in database
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
        # find user by username or email
        user = await self.find_user_by_username_or_email(login_data.username)
        if user is None or not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid username or password")

        if not user.is_active:
            raise ValueError("Invalid username or password")

        # generate jwt access token
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
        )

        # generate random refresh token and hash it with sha256
        raw_refresh_token = create_refresh_token()
        token_hash = hash_refresh_token(raw_refresh_token)

        # calculate expiry time in utc
        now = datetime.now(timezone.utc)
        expire_days = getattr(settings, "REFRESH_TOKEN_EXPIRY_TIME", 15)
        expires_at = now + timedelta(days=expire_days)

        # save the hashed refresh token in database
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=now,
            is_revoked=False,
            ip_address=ip,
            user_agent=user_agent,
        )
        self.repository.db.add(token_record)
        await self.repository.db.commit()

        token_payload = {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "bearer",
        }
        return token_payload, raw_refresh_token

    async def refresh_token(
        self,
        raw_refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[dict[str, str], str]:
        # hash incoming token to find it in the database
        incoming_hash = hash_refresh_token(raw_refresh_token)

        statement = select(RefreshToken).where(RefreshToken.token_hash == incoming_hash)
        result = await self.repository.db.execute(statement)
        token_record = result.scalar_one_or_none()

        # check if token exists
        if not token_record:
            raise ValueError("Invalid refresh token")

        # check if token is already revoked
        if token_record.is_revoked:
            raise ValueError("Refresh token has been revoked")

        # check if token has expired
        now = datetime.now(timezone.utc)
        if token_record.expires_at <= now:
            token_record.is_revoked = True
            await self.repository.db.commit()
            raise ValueError("Refresh token has expired")

        # check if user exists and is active
        user = await self.repository.get_user_by_id(str(token_record.user_id))
        if not user or not user.is_active:
            token_record.is_revoked = True
            await self.repository.db.commit()
            raise ValueError("User account is inactive or not found")

        # revoke old token (simple rotation: old token is used once)
        token_record.is_revoked = True

        # generate new refresh token and hash it
        new_raw_token = create_refresh_token()
        new_hash = hash_refresh_token(new_raw_token)
        expire_days = getattr(settings, "REFRESH_TOKEN_EXPIRY_TIME", 15)
        new_expires_at = now + timedelta(days=expire_days)

        new_token_record = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_expires_at,
            created_at=now,
            is_revoked=False,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.repository.db.add(new_token_record)

        # link replaced_by to trace the rotation
        token_record.replaced_by = new_token_record.id

        # generate new access token
        new_access_token = create_access_token(
            user_id=user.id,
            username=user.username,
        )

        # save all changes in the database
        await self.repository.db.commit()

        token_payload = {
            "access_token": new_access_token,
            "refresh_token": new_raw_token,
            "token_type": "bearer",
        }
        return token_payload, new_raw_token

    async def revoke_token(self, raw_refresh_token: str) -> None:
        # revoke single refresh token when user logs out
        incoming_hash = hash_refresh_token(raw_refresh_token)
        statement = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == incoming_hash)
            .values(is_revoked=True)
        )
        await self.repository.db.execute(statement)
        await self.repository.db.commit()

    async def change_password(
        self,
        user: User,
        data: PasswordChangeRequest,
    ) -> User:
        # verify user current password first
        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCurrentPassword("Current password is incorrect")

        try:
            # update user password and password changed time
            user.password_hash = hash_password(data.new_password)
            user.password_changed_at = datetime.now(timezone.utc)

            # revoke all active refresh tokens for this user
            statement = (
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == str(user.id),
                    RefreshToken.is_revoked.is_(False),
                )
                .values(is_revoked=True)
            )
            await self.repository.db.execute(statement)

            await self.repository.db.commit()
            await self.repository.db.refresh(user)
            return user
        except Exception:
            await self.repository.db.rollback()
            raise
