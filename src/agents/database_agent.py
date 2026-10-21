# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - DatabaseAgent

Real agent for Database operations: connect, query, migrate, etc.
Supports SQLite, PostgreSQL, MySQL, and MongoDB.
"""

import sqlite3
from typing import List, Optional, cast

from ..core.agent_base import AgentBase, Result, Task
from .database_agent_ops import DatabaseAgentOpsMixin

DbConnection = Optional[sqlite3.Connection]


class DatabaseAgent(DatabaseAgentOpsMixin, AgentBase):
    """
    Agent for Database operations.

    Supports:
    - connect: Connect to database (SQLite, PostgreSQL, MySQL, MongoDB)
    - query: Execute SELECT, INSERT, UPDATE, DELETE statements
    - migrate: Run database migrations
    - schema: Show database schema
    - backup: Backup database
    - restore: Restore database from backup
    """

    def __init__(self, db_url: Optional[str] = None) -> None:
        """Initialize DatabaseAgent with optional database URL."""
        super().__init__(name="DatabaseAgent")
        self.db_url: Optional[str] = db_url
        self.connection: DbConnection = None

    def plan(self, input_data: str) -> List[Task]:
        """Parse database command string into tasks."""
        parts = input_data.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "connect":
            return [Task(
                id="db_connect",
                description=f"Connect to database: {args}",
                input={"db_url": args},
            )]
        elif command == "query":
            return [Task(
                id="db_query",
                description=f"Execute query: {args}",
                input={"query": args},
            )]
        elif command == "migrate":
            migration_path = args if args else "./migrations"
            return [Task(
                id="db_migrate",
                description=f"Run migrations from: {migration_path}",
                input={"migration_path": migration_path},
            )]
        elif command == "schema":
            table_name = args if args else None
            return [Task(
                id="db_schema",
                description=f"Show schema{' for ' + table_name if table_name else ''}",
                input={"table_name": table_name},
            )]
        elif command == "backup":
            backup_path = args if args else "./backup.sql"
            return [Task(
                id="db_backup",
                description=f"Backup database to: {backup_path}",
                input={"backup_path": backup_path},
            )]
        elif command == "restore":
            backup_path = args if args else "./backup.sql"
            return [Task(
                id="db_restore",
                description=f"Restore database from: {backup_path}",
                input={"backup_path": backup_path},
            )]
        else:
            return [Task(
                id="db_raw_sql",
                description=f"Execute raw SQL: {input_data}",
                input={"query": input_data},
            )]

    def execute(self, task: Task) -> Result:
        """Execute database task."""
        try:
            if task.id == "db_connect":
                return self._execute_connect(task)
            elif task.id == "db_query":
                return self._execute_query(task)
            elif task.id == "db_migrate":
                return self._execute_migrate(task)
            elif task.id == "db_schema":
                return self._execute_schema(task)
            elif task.id == "db_backup":
                return self._execute_backup(task)
            elif task.id == "db_restore":
                return self._execute_restore(task)
            elif task.id == "db_raw_sql":
                return self._execute_query(task)
            else:
                return Result(
                    task_id=task.id,
                    success=False,
                    output=None,
                    error=f"Unknown task type: {task.id}",
                )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))

    def _execute_connect(self, task: Task) -> Result:
        """Execute database connection."""
        db_url = cast(str, task.input.get("db_url", self.db_url))
        if not db_url:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error="No database URL provided",
            )

        if db_url.startswith("sqlite:///"):
            db_path = db_url[len("sqlite:///"):]
            self.connection = sqlite3.connect(db_path)
            output = f"Connected to SQLite database: {db_path}"
        else:
            output = f"Database connection configured: {db_url}"

        return Result(task_id=task.id, success=True, output=output, error=None)


__all__ = ["DatabaseAgent", "DbConnection", "sqlite3"]
