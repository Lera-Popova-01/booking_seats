import logging
import time
from typing import Any, Dict

import jwt
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routers import main_router
from src.core.config import settings
from src.core.db import AsyncSessionLocal
from src.core.logging_setup import (
    clear_log_user_context,
    set_log_user_context,
    setup_logging,
)
from src.models.user import User

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_title,
    version="0.0.2",
)
app.include_router(main_router)


async def _resolve_log_user_from_token(request: Request) -> None:
    """Заполнить user-контекст лога из Bearer-токена, если он есть."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        clear_log_user_context()
        return

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        clear_log_user_context()
        return

    try:
        payload = jwt.decode(
            token,
            settings.secret_key_str(),
            algorithms=[settings.algorithm or "HS256"],
            audience="fastapi-users:auth",
        )
        user_id = payload.get("sub")
        if not user_id:
            clear_log_user_context()
            return
    except Exception:
        clear_log_user_context()
        return

    try:
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            if user is None:
                set_log_user_context(user_id=str(user_id), username="SYSTEM")
                return
            set_log_user_context(
                user_id=str(user.id),
                username=user.username,
            )
    except Exception:
        # На лог-контекст не должны влиять ошибки БД.
        set_log_user_context(user_id=str(user_id), username="SYSTEM")


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: Any,
) -> Response:
    """Логирование HTTP-запросов/ответов с user-контекстом."""
    await _resolve_log_user_from_token(request)
    started_at = time.perf_counter()
    logger.info(
        "HTTP request started: method=%s path=%s",
        request.method,
        request.url.path,
    )

    response = None
    try:
        response = await call_next(request)
        return response  # noqa: RET504
    except Exception:
        logger.exception(
            "HTTP request failed: method=%s path=%s",
            request.method,
            request.url.path,
        )
        raise
    finally:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        status_code = response.status_code if response is not None else 500
        logger.info(
            "HTTP request finished: method=%s path=%s "
            "status=%s duration_ms=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )
        clear_log_user_context()


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Проверка работоспособности API."""
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException,
) -> JSONResponse:
    """Обработчик HTTP исключений для кастомизации ответа."""
    logger.warning(
        "HTTP exception: method=%s path=%s status=%s detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        payload = detail
    else:
        payload = {"code": exc.status_code, "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Обработчик ошибок валидации."""
    logger.warning(
        "Validation error: method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )

    error = exc.errors()[0]
    message = error.get("msg", "Ошибка валидации данных")

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": message,
        },
    )
