# Live in a Week — Backend

FastAPI + PostgreSQL backend for the [Live in a Week](https://github.com/joshi-kaushal/live-in-a-week) browser extension.

## Quick Start

```bash
# Start everything (PostgreSQL + PgAdmin + Backend)
docker compose up --build

# API docs
open http://localhost:8000/docs

# PgAdmin
open http://localhost:5050
# Login: admin@liaw.dev / admin
```

## Stack

- **FastAPI** — async Python API
- **PostgreSQL 16** — primary database
- **SQLAlchemy 2.0** — async ORM
- **Alembic** — database migrations
- **Docker Compose** — local dev environment

## Environment

Copy `.env.example` to `.env` and fill in your Meta Cloud API keys.

## Migrations

```bash
# Generate a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head
```
