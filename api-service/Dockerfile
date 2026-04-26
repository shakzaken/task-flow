FROM node:22-alpine AS frontend-builder

WORKDIR /workspace/frontend-service

COPY frontend-service/package.json frontend-service/package-lock.json ./
RUN npm ci

COPY frontend-service/ ./
RUN npm run build


FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY api-service/pyproject.toml api-service/uv.lock api-service/alembic.ini ./
COPY api-service/app ./app
COPY api-service/migrations ./migrations

RUN uv sync --frozen --no-dev


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app
COPY --from=frontend-builder /workspace/frontend-service/dist ./app/static

EXPOSE 8000

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
