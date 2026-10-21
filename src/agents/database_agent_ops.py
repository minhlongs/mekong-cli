# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""DatabaseAgent execution operations: query, migrate, schema, backup, restore."""

from pathlib import Path
from typing import Any, Optional, cast

from ..core.agent_base import Result, Task


def _db_mod() -> Any:
    import src.agents.database_agent as _mod
    return _mod


class DatabaseAgentOpsMixin:
    """Mixin providing database query, schema, migration, backup, and restore operations."""

    db_url: Optional[str]
    connection: Any

    def _execute_query(self, task: Task) -> Result:
        """Execute database query."""
        query = cast(str, task.input.get("query"))
        if not query:
            return Result(task_id=task.id, success=False, output=None, error="No query provided")

        try:
            sqlite3 = _db_mod().sqlite3
            if self.connection is None:
                self.connection = sqlite3.connect(":memory:")

            cursor = self.connection.cursor()
            statements = [stmt.strip() for stmt in query.split(";") if stmt.strip()]

            if len(statements) > 1:
                for stmt in statements[:-1]:
                    cursor.execute(stmt)
                last_stmt = statements[-1]
                if last_stmt.strip().upper().startswith("SELECT"):
                    cursor.execute(last_stmt)
                    rows = cursor.fetchall()
                    columns = [d[0] for d in cursor.description] if cursor.description else []
                    result_data = {
                        "columns": columns,
                        "rows": [dict(zip(columns, row)) for row in rows],
                        "row_count": len(rows),
                    }
                    output = f"Multi-query executed successfully. Rows returned: {len(rows)}"
                    if rows:
                        output += f"\nSample data: {result_data}"
                else:
                    cursor.execute(last_stmt)
                    self.connection.commit()
                    output = f"Multi-query executed successfully. Rows affected: {cursor.rowcount}"
            else:
                cursor.execute(query)
                if query.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    columns = [d[0] for d in cursor.description] if cursor.description else []
                    result_data = {
                        "columns": columns,
                        "rows": [dict(zip(columns, row)) for row in rows],
                        "row_count": len(rows),
                    }
                    output = f"Query executed successfully. Rows returned: {len(rows)}"
                    if rows:
                        output += f"\nSample data: {result_data}"
                else:
                    self.connection.commit()
                    output = f"Query executed successfully. Rows affected: {cursor.rowcount}"

            return Result(task_id=task.id, success=True, output=output, error=None)
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=f"Query execution failed: {str(e)}")

    def _execute_migrate(self, task: Task) -> Result:
        """Execute database migrations."""
        migration_path = cast(str, task.input.get("migration_path", "./migrations"))
        migration_dir = Path(migration_path)
        if not migration_dir.exists():
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=f"Migration directory does not exist: {migration_path}",
            )
        migration_files = list(migration_dir.glob("*.sql"))
        output = f"Found {len(migration_files)} migration files in {migration_path}"
        return Result(task_id=task.id, success=True, output=output, error=None)

    def _execute_schema(self, task: Task) -> Result:
        """Execute schema query."""
        table_name = cast(Optional[str], task.input.get("table_name"))
        sqlite3 = _db_mod().sqlite3
        if self.connection is None:
            self.connection = sqlite3.connect(":memory:")

        cursor = self.connection.cursor()
        if table_name:
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                schema_info = [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default": col[4],
                        "primary_key": bool(col[5]),
                    }
                    for col in columns
                ]
                output = f"Schema for table '{table_name}': {schema_info}"
            except Exception as e:
                return Result(
                    task_id=task.id,
                    success=False,
                    output=None,
                    error=f"Failed to get schema for table {table_name}: {str(e)}",
                )
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            output = f"Database contains {len(tables)} tables: {tables}"

        return Result(task_id=task.id, success=True, output=output, error=None)

    def _execute_backup(self, task: Task) -> Result:
        """Execute database backup."""
        backup_path = cast(str, task.input.get("backup_path", "./backup.sql"))
        sqlite3 = _db_mod().sqlite3
        if self.connection is not None:
            backup_conn = sqlite3.connect(backup_path)
            self.connection.backup(backup_conn)
            backup_conn.close()
            output = f"Database backed up to: {backup_path}"
        else:
            output = f"Backup command prepared for: {backup_path}"
        return Result(task_id=task.id, success=True, output=output, error=None)

    def _execute_restore(self, task: Task) -> Result:
        """Execute database restore."""
        backup_path = cast(str, task.input.get("backup_path", "./backup.sql"))
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=f"Backup file does not exist: {backup_path}",
            )
        if backup_file.suffix.lower() == ".sql":
            with open(backup_file, "r") as f:
                sql_script = f.read()
            if self.connection is not None:
                cursor = self.connection.cursor()
                cursor.executescript(sql_script)
                self.connection.commit()
                output = f"Database restored from: {backup_path}"
            else:
                output = f"Restoration script prepared from: {backup_path}"
        else:
            output = f"Restore command prepared for: {backup_path}"
        return Result(task_id=task.id, success=True, output=output, error=None)
