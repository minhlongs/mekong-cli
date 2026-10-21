# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite-backed durable goal store."""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

from .models import (
    AcceptanceCriterion,
    AgentRole,
    Checkpoint,
    Goal,
    GoalStatus,
    GoalTask,
    TaskStatus,
    VerificationRun,
)
from .store_queries import GoalStoreQueriesMixin
from .store_schema import GOAL_STORE_SCHEMA_SQL, GoalStoreSchemaMixin

_logger = logging.getLogger(__name__)

# Goals are user-level state, so the canonical store lives under the home
# directory and the same goals stay visible from every working directory.
# Runs that still have a repo-local `.mekong/goals.sqlite3` keep reading from
# it, so historical goals are never silently dropped. Set MEKONG_GOAL_DB to
# pin an explicit path.
DEFAULT_GOAL_DB_NAME = "goals.sqlite3"


def resolve_goal_db_path(db_path: str | Path | None = None) -> Path:
    """Resolve the goal store path deterministically, independent of CWD.

    Precedence: explicit argument, MEKONG_GOAL_DB, an existing repo-local
    store, then the home-anchored canonical location.
    """
    if db_path:
        return Path(db_path).absolute()

    env_override = os.environ.get("MEKONG_GOAL_DB")
    if env_override:
        return Path(env_override).absolute()

    # A repo-local store is a separate history, not a shadow copy of the home
    # one, so it keeps winning while it exists. Choosing home over it would
    # hide every goal created from that directory.
    local_path = (Path.cwd() / ".mekong" / DEFAULT_GOAL_DB_NAME)
    if local_path.is_file():
        _logger.debug("using repo-local goal store at %s", local_path)
        return local_path

    return Path.home() / ".mekong" / DEFAULT_GOAL_DB_NAME


class SQLiteGoalStore(GoalStoreSchemaMixin, GoalStoreQueriesMixin):
    """Durable local-first store for goals, tasks, checkpoints, events, and gates."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = resolve_goal_db_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._init_schema()


__all__ = [
    "SQLiteGoalStore",
    "DEFAULT_GOAL_DB_NAME",
    "resolve_goal_db_path",
    "GoalStoreSchemaMixin",
    "GoalStoreQueriesMixin",
    "GOAL_STORE_SCHEMA_SQL",
    "AcceptanceCriterion",
    "AgentRole",
    "Checkpoint",
    "Goal",
    "GoalStatus",
    "GoalTask",
    "TaskStatus",
    "VerificationRun",
]
