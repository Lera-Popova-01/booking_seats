# Шаблон для проектов со стилизатором Ruff

## Основное

1. Базовая версия Python - 3.11.
2. В файле `requirements_style.txt` находятся зависимости для стилистики.
3. В каталоге `src` находится базовая структура проекта
4. В файле `src/requirements.txt` прописываются базовые зависимости.
5. В каталоге `infra` находятся настроечные файлы проекта. Здесь же размещать файлы для docker compose.
6. Для фоновых задач используется Celery, базовая конфигурация находится в `src/tasks/celery_app.py`.

## Фоновые задачи и уведомления администратора

Для работы Celery требуется брокер сообщений (например, Redis).

Пример запуска воркера Celery (после установки зависимостей из `src/requirements.txt`):

```shell
PYTHONPATH=. celery -A src.tasks.celery_app.celery_app worker --loglevel=info
```

Команда запускается **из корня репозитория** (каталог, где лежит папка `src`).

В модуле `src/notifications/tasks.py` реализованы задачи:

- `debug_task` — тестовая задача для проверки работы Celery;
- `send_admin_booking_created` — заготовка уведомления администратора о создании бронирования;
- `send_admin_booking_updated` — заготовка уведомления администратора об изменении бронирования.


## Стилистика

Для стилизации кода используется пакеты `Ruff` и `Pre-commit`

Проверка стилистики кода осуществляется командой
```shell
ruff check
```

Если одновременно надо пофиксить то, что можно поиксить автоматически, то добавляем параметр `--fix`
```shell
ruff check --fix
```

Что бы стилистика автоматически проверялась и поправлялась при комитах надо добавить hook pre-commit к git

```shell
pre-commit install
```

## Локальная разработка (Docker Compose)

Команды выполняются из корня репозитория.

1. Подготовить файл переменных окружения:
```shell
cp infra/.env infra/.env
```

2. Запустить dev-контур:
```shell
docker compose -f infra/docker-compose.yml up --build
```

3. Проверить API:
- `http://localhost:8000/health`

В dev-режиме исходники из `src` и миграции примонтированы в контейнер, поэтому `uvicorn --reload` подхватывает изменения без пересборки образа.

### Portainer в dev (опционально)

```shell
docker compose -f infra/docker-compose.yml --profile ops up --build
```

## Запуск в production (Docker Compose + Nginx)

Команды выполняются из корня репозитория.

1. Подготовить файл переменных окружения:
```shell
cp infra/.env infra/.env
```

2. Убедиться, что в `infra/.env` заданы обязательные значения:
- `FIRST_SUPERUSER_EMAIL`
- `FIRST_SUPERUSER_PASSWORD`
- `FIRST_SUPERUSER_USERNAME` (опционально, по умолчанию `admin`)

3. Запустить production-контур:
```shell
docker compose -f infra/docker-compose.prod.yml up -d
```

4. Проверить доступность:
- API через Nginx: `http://localhost/health`
- Nginx health endpoint: `http://localhost/nginx-health`

5. Остановить контур:
```shell
docker compose -f infra/docker-compose.prod.yml down
```

### Запуск с Portainer (опционально)

```shell
docker compose -f infra/docker-compose.prod.yml --profile ops up -d
```

Portainer будет доступен по адресам:
- `https://localhost:9443`
- `http://localhost:9000`

## CI/CD деплой (GitHub Actions)

Workflow `.github/workflows/deploy.yml` на каждый push в `develop`:

1. Собирает backend-образ из `src/Dockerfile` и пушит в DockerHub.
2. Собирает gateway-образ из `infra/nginx/Dockerfile` и пушит в DockerHub.
3. Копирует `infra/docker-compose.prod.yml` на сервер.
4. На сервере создаёт `infra/.env` из секрета `PROD_ENV_FILE`.
5. Выполняет `docker compose pull` и `docker compose up -d`.

Для работы workflow нужны secrets:

- `DOCKER_USERNAME`, `DOCKER_PASSWORD`
- `HOST`, `USER`, `SSH_KEY`
