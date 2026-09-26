from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",
        # "http://localhost:5173",
        # "http://127.0.0.1:3000",
        # "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(todo_router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Todo API is running"}