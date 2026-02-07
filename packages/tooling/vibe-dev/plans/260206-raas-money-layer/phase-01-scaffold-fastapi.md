# Phase 1: Scaffold FastAPI Service

**Status:** Pending
**Priority:** High
**Context:** Foundation for the Money Layer.

## Context Links
- [Master Plan](./plan.md)
- [Researcher Report](../reports/researcher-260206-2159-stripe-credits-fastapi.md)

## Overview
We need to establish the `apps/api` service using Python and FastAPI. This service will act as the "Wallet" for the platform. It must be production-ready from day one, with proper Docker containerization and asynchronous database drivers.

## Requirements
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Server:** Uvicorn / Gunicorn
- **Database Driver:** `asyncpg` + `SQLAlchemy 2.0` (Async)
- **Dependency Management:** `poetry` or `pip` (requirements.txt)
- **Containerization:** Dockerfile optimized for Python.

## Implementation Steps

1.  **Project Initialization**
    - Create `apps/api` directory.
    - Initialize Python project (pyproject.toml).
    - Install dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `asyncpg`, `pydantic-settings`, `stripe`.

2.  **Directory Structure**
    ```text
    apps/api/
    ├── src/
    │   ├── main.py
    │   ├── config.py
    │   ├── database.py
    │   ├── routers/
    │   │   └── health.py
    │   └── services/
    ├── alembic/
    ├── Dockerfile
    └── pyproject.toml
    ```

3.  **Database Configuration**
    - Create `src/database.py` with `AsyncSession` setup.
    - Configure `alembic` for async migrations.

4.  **Docker Setup**
    - Create `Dockerfile`.
    - Update root `infrastructure/docker-compose.yml` to include the new `api` service.

5.  **Health Check**
    - Implement `GET /health` endpoint returning DB connection status.

## Todo List
- [ ] Create `apps/api` directory structure.
- [ ] Create `pyproject.toml` and install dependencies.
- [ ] Implement `src/config.py` (Env vars).
- [ ] Implement `src/database.py` (Async engine).
- [ ] Initialize Alembic (`alembic init -t async`).
- [ ] Create `Dockerfile`.
- [ ] Update `docker-compose.yml`.
- [ ] Verify `GET /health` returns 200.
