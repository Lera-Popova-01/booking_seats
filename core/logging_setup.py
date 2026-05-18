import logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from src.core.config import settings

_SYSTEM_USER = "SYSTEM"
_USER_ID_CTX: ContextVar[str] = ContextVar(
    "log_user_id",
    default=_SYSTEM_USER,
)
_USERNAME_CTX: ContextVar[str] = ContextVar(
    "log_username",
    default=_SYSTEM_USER,
)


class UserContextFilter(logging.Filter):
    """Добавляет user-контекст в каждую запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Добавляет user_id и username в запись лога."""
        record.user_id = getattr(record, "user_id", _USER_ID_CTX.get())
        record.username = getattr(record, "username", _USERNAME_CTX.get())
        return True


def set_log_user_context(*, user_id: str | None, username: str | None) -> None:
    """Установить контекст пользователя для текущего async-контекста."""
    _USER_ID_CTX.set(user_id or _SYSTEM_USER)
    _USERNAME_CTX.set(username or _SYSTEM_USER)


def clear_log_user_context() -> None:
    """Сбросить контекст пользователя к SYSTEM."""
    set_log_user_context(user_id=_SYSTEM_USER, username=_SYSTEM_USER)


def _configure_root_logger(
    *,
    level: str,
    log_file_path: Path,
    max_bytes: int,
    backup_count: int,
) -> None:
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)s | user=%(username)s(%(user_id)s) "
            "| %(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    context_filter = UserContextFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)

    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.upper())
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False


def setup_logging() -> None:
    """Настроить централизованное логирование в файл и консоль."""
    if getattr(setup_logging, "_configured", False):
        return

    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / settings.log_file_name

    _configure_root_logger(
        level=settings.log_level,
        log_file_path=log_file_path,
        max_bytes=settings.log_file_max_bytes,
        backup_count=settings.log_file_backup_count,
    )
    setup_logging._configured = True

    logger = logging.getLogger(__name__)
    logger.info(
        "Логирование настроено: file=%s level=%s max_bytes=%s backups=%s",
        str(log_file_path),
        settings.log_level,
        settings.log_file_max_bytes,
        settings.log_file_backup_count,
    )


def redact_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """Скрыть секретные поля перед записью в лог."""
    redacted: dict[str, Any] = {}
    sensitive_markers = ("password", "secret", "token", "hash")

    for key, value in data.items():
        if any(marker in key.lower() for marker in sensitive_markers):
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted
