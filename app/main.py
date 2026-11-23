from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.base import Base
from app.db.session import engine
from app.modules.auth.router import router as auth_router
from app.modules.tasks.router import router as tasks_router
from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        Base.metadata.create_all(engine)
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="fast-server",
    description="This is a sample FastAPI application.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tasks_router)


@app.exception_handler(RequestValidationError)
async def redact_validation_input(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})
