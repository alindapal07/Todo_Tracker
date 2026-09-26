import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from db.base import Base
# Import all models so metadata knows about them
import models.refreshToken_model  # noqa: F401
import models.todo_model  # noqa: F401
import models.user_model  # noqa: F401


logger = logging.getLogger("api.db")


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

        # Ensure required columns exist for existing tables
        try:
            await connection.execute(
                text('ALTER TABLE "user-table" ADD COLUMN IF NOT EXISTS username VARCHAR(50);')
            )
            await connection.execute(
                text('ALTER TABLE "user-table" ADD COLUMN IF NOT EXISTS name VARCHAR(50);')
            )
            await connection.execute(
                text('ALTER TABLE "user-table" ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;')
            )
            await connection.execute(
                text('UPDATE "user-table" SET username = COALESCE(username, name, email) WHERE username IS NULL;')
            )
            await connection.execute(
                text('UPDATE "user-table" SET is_active = TRUE WHERE is_active IS NULL;')
            )
        except Exception as exc:
            logger.warning("user-table column migration note: %s", exc)

        try:
            await connection.execute(
                text('ALTER TABLE todos ADD COLUMN IF NOT EXISTS user_id VARCHAR REFERENCES "user-table"(id);')
            )
            await connection.execute(
                text('UPDATE todos SET user_id = (SELECT id FROM "user-table" LIMIT 1) WHERE user_id IS NULL;')
            )
        except Exception as exc:
            logger.warning("todos table column migration note: %s", exc)

        try:
            await connection.execute(
                text('ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS replaced_by UUID;')
            )
        except Exception as exc:
            logger.warning("refresh_tokens table column migration note: %s", exc)
