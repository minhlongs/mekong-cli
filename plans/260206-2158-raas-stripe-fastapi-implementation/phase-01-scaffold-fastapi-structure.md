# Phase 1: Scaffold FastAPI & Core Structure

**Status:** Pending
**Priority:** High

## Overview
Initialize the FastAPI project with a scalable, production-ready directory structure. This foundation supports future growth by separating concerns into routers, services, and data layers.

## Requirements
- Python 3.10+
- FastAPI, Uvicorn, SQLAlchemy, Pydantic-Settings
- PostgreSQL (driver: asyncpg)

## Architecture
Using the structure recommended in the research report:
```
app/
├── api/ v1/ endpoints/
├── core/ (config, security)
├── db/ (session, base)
├── models/
├── schemas/
├── services/
└── main.py
```

## Implementation Steps

1.  **Project Initialization**
    - Create `pyproject.toml` or `requirements.txt`.
    - Dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `asyncpg`, `pydantic-settings`, `stripe`.

2.  **Core Configuration (`app/core/config.py`)**
    - Use `pydantic_settings.BaseSettings`.
    - Define: `DATABASE_URL`, `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `API_V1_STR`.

3.  **Database Setup (`app/db/`)**
    - `session.py`: Configure `AsyncSession` and `create_async_engine`.
    - `base.py`: Create `Base` class for models.

4.  **Application Entry Point (`app/main.py`)**
    - Initialize `FastAPI` app.
    - Include API router.
    - Configure CORS.

## Todo List
- [ ] Create directory structure
- [ ] Create `requirements.txt` / `pyproject.toml`
- [ ] Implement `app/core/config.py`
- [ ] Implement `app/db/session.py`
- [ ] Implement `app/main.py`
- [ ] Verify server starts with `uvicorn`
