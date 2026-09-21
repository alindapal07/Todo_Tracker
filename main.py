from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.todo_route import router as todo_router
from db.session import engine
from db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title="Todo API",
    description="Basic project on todo app",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(todo_router)


@app.get("/")
def root():
    return {"message": "Todo API is running"}