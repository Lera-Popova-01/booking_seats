from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_title: Optional[str] = Field(
        default=None, description='Название приложения',
    )
    debug: Optional[bool] = Field(default=None, description='Режим отладки')

    db_host: Optional[str] = Field(
        default=None, description='Хост базы данных',
    )
    db_port: Optional[int] = Field(
        default=None, description='Порт базы данных',
    )
    db_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('DB_NAME', 'POSTGRES_DB'),
        description='Название базы данных',
    )
    db_user: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('DB_USER', 'POSTGRES_USER'),
        description='Пользователь базы данных',
    )
    db_password: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices('DB_PASSWORD', 'POSTGRES_PASSWORD'),
        description='Пароль базы данных',
    )

    secret_key: Optional[SecretStr] = Field(
        default=None, description='Секретный ключ для JWT',
    )
    algorithm: Optional[str] = Field(
        default=None, description='Алгоритм шифрования JWT',
    )
    access_token_expire_minutes: Optional[int] = Field(
        default=None, description='Время жизни access токена в минутах.',
    )
    celery_broker_url: Optional[str] = Field(
        default=None, description='URL брокера Celery/RabbitMQ',
    )
    celery_result_backend: Optional[str] = Field(
        default=None, description='Result backend для Celery',
    )
    celery_timezone: str = Field(
        default='UTC',
        description='Время Celery и расчёта ETA для работы напоминаний',
    )
    booking_timezone: str = Field(
        default='Europe/Moscow',
        description='Часовой пояс локального времени бронирований',
    )
    log_level: str = Field(default='INFO', description='Уровень логирования')
    log_dir: str = Field(
        default='logs',
        description='Папка для лог-файлов приложения',
    )
    log_file_name: str = Field(
        default='app.log',
        description='Имя основного лог-файла',
    )
    log_file_max_bytes: int = Field(
        default=5_242_880,
        description='Максимальный размер лог-файла перед ротацией',
    )
    log_file_backup_count: int = Field(
        default=5,
        description='Количество файлов ротации логов',
    )
    smtp_host: str | None = Field(
        default=None,
        description='SMTP хост для отправки email-уведомлений',
    )
    smtp_port: int = Field(
        default=587,
        description='SMTP порт для отправки email-уведомлений',
    )
    smtp_user: str | None = Field(
        default=None,
        description='Логин SMTP',
    )
    smtp_password: SecretStr | None = Field(
        default=None,
        description='Пароль SMTP',
    )
    smtp_from_email: str | None = Field(
        default=None,
        description='Email отправителя уведомлений',
    )
    smtp_use_tls: bool = Field(
        default=True,
        description='Использовать STARTTLS для SMTP',
    )

    first_superuser_email: Optional[str] = Field(
        default=None,
        description='Email первого суперпользователя',
    )
    first_superuser_password: Optional[str] = Field(
        default=None,
        description='Пароль первого суперпользователя',
    )
    first_superuser_username: Optional[str] = Field(
        default='admin',
        description='Имя пользователя первого суперпользователя',
    )
    first_superuser_phone: Optional[str] = Field(
        default=None,
        description='Телефон первого суперпользователя',
    )

    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parents[1] / '.env'),
            str(Path(__file__).resolve().parents[2] / 'infra/.env'),
        ),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    def secret_key_str(self) -> str:
        """Получить секретный ключ как строку."""
        if self.secret_key is None:
            raise ValueError('SECRET_KEY не задан в конфигурации')
        return self.secret_key.get_secret_value()

    @property
    def database_url(self) -> str:
        """Получить URL для подключения к базе данных."""
        if self.db_user is None:
            raise ValueError('DB_USER не задан')
        if self.db_password is None:
            raise ValueError('DB_PASSWORD не задан')
        if self.db_host is None:
            raise ValueError('DB_HOST не задан')
        if self.db_port is None:
            raise ValueError('DB_PORT не задан')
        if self.db_name is None:
            raise ValueError('DB_NAME не задан')
        return (
            f'postgresql+asyncpg://{self.db_user}:'
            f'{self.db_password.get_secret_value()}'
            f'@{self.db_host}:{self.db_port}/{self.db_name}'
        )


settings = Settings()
