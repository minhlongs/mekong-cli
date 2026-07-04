#!/usr/bin/env python3
"""Run ZenPay database migrations."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alembic.config import Config
from alembic import command

def run_migrations():
    """Run Alembic migrations."""
    # Set environment
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://zenpay:zenpay@localhost:5432/zenpay")

    # Create Alembic config
    alembic_cfg = Config("src/zenpay/migrations/alembic.ini")
    alembic_cfg.set_main_option("script_location", "src/zenpay/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

    # Run upgrade
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully")

if __name__ == "__main__":
    run_migrations()
