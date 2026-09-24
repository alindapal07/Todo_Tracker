from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth_route import router as auth_router
from api.todo_route import router as todo_router
from db.init_db import init_db
from db.session import engine
from middleware.request_timing import RequestTimingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(engine)
    yield


app = FastAPI(
    title="Todo API",
    description="Clean, production-ready Todo API with JWT Authentication and Authorization",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestTimingMiddleware)

app.include_router(auth_router)
app.include_router(todo_router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Todo API is running"}