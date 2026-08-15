"""Tests for DatabaseAgent — covers connect, query, migrate, schema, backup, restore."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.database_agent import DatabaseAgent
from src.core.agent_base import Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(task_id: str, **input_kwargs) -> Task:
    return Task(id=task_id, description="test", input=dict(**input_kwargs))


# ---------------------------------------------------------------------------
# plan()
# ---------------------------------------------------------------------------

class TestPlan:
    def setup_method(self):
        self.agent = DatabaseAgent()

    def test_plan_connect(self):
        tasks = self.agent.plan("connect sqlite:///test.db")
        assert len(tasks) == 1
        assert tasks[0].id == "db_connect"
        assert tasks[0].input["db_url"] == "sqlite:///test.db"

    def test_plan_query(self):
        tasks = self.agent.plan("query SELECT 1")
        assert len(tasks) == 1
        assert tasks[0].id == "db_query"
        assert tasks[0].input["query"] == "SELECT 1"

    def test_plan_migrate_default_path(self):
        tasks = self.agent.plan("migrate")
        assert tasks[0].id == "db_migrate"
        assert tasks[0].input["migration_path"] == "./migrations"

    def test_plan_migrate_custom_path(self):
        tasks = self.agent.plan("migrate ./db/migrations")
        assert tasks[0].input["migration_path"] == "./db/migrations"

    def test_plan_schema_no_table(self):
        tasks = self.agent.plan("schema")
        assert tasks[0].id == "db_schema"
        assert tasks[0].input["table_name"] is None

    def test_plan_schema_with_table(self):
        tasks = self.agent.plan("schema users")
        assert tasks[0].input["table_name"] == "users"

    def test_plan_backup_default(self):
        tasks = self.agent.plan("backup")
        assert tasks[0].id == "db_backup"
        assert tasks[0].input["backup_path"] == "./backup.sql"

    def test_plan_backup_custom(self):
        tasks = self.agent.plan("backup /tmp/my.sql")
        assert tasks[0].input["backup_path"] == "/tmp/my.sql"

    def test_plan_restore_default(self):
        tasks = self.agent.plan("restore")
        assert tasks[0].id == "db_restore"
        assert tasks[0].input["backup_path"] == "./backup.sql"

    def test_plan_restore_custom(self):
        tasks = self.agent.plan("restore /tmp/my.sql")
        assert tasks[0].input["backup_path"] == "/tmp/my.sql"

    def test_plan_raw_sql_fallback(self):
        tasks = self.agent.plan("CREATE TABLE foo (id INTEGER)")
        assert tasks[0].id == "db_raw_sql"
        assert "CREATE TABLE" in tasks[0].input["query"]

    def test_plan_case_insensitive_command(self):
        # plan() does .lower() so "QUERY" matches "query" → db_query
        tasks = self.agent.plan("QUERY SELECT 1")
        assert tasks[0].id == "db_query"
        assert tasks[0].input["query"] == "SELECT 1"


# ---------------------------------------------------------------------------
# execute() — connect
# ---------------------------------------------------------------------------

class TestExecuteConnect:
    def setup_method(self):
        self.agent = DatabaseAgent()

    def test_connect_sqlite_memory(self):
        task = make_task("db_connect", db_url="sqlite:///:memory:")
        result = self.agent.execute(task)
        assert result.success is True
        assert "sqlite" in result.output.lower()

    def test_connect_sqlite_file(self, tmp_path):
        db_file = tmp_path / "test.db"
        task = make_task("db_connect", db_url=f"sqlite:///{db_file}")
        result = self.agent.execute(task)
        assert result.success is True
        assert str(db_file) in result.output
        # Cleanup
        if self.agent.connection:
            self.agent.connection.close()

    def test_connect_no_url_returns_error(self):
        task = make_task("db_connect", db_url="")
        result = self.agent.execute(task)
        assert result.success is False
        assert "No database URL" in result.error

    def test_connect_non_sqlite_url(self):
        task = make_task("db_connect", db_url="postgresql://user:pass@localhost/mydb")
        result = self.agent.execute(task)
        assert result.success is True
        assert "postgresql" in result.output

    def test_connect_uses_instance_db_url_as_fallback(self):
        agent = DatabaseAgent(db_url="sqlite:///:memory:")
        task = make_task("db_connect")  # no db_url in input
        result = agent.execute(task)
        assert result.success is True


# ---------------------------------------------------------------------------
# execute() — query
# ---------------------------------------------------------------------------

class TestExecuteQuery:
    def setup_method(self):
        self.agent = DatabaseAgent()

    def test_select_query_no_connection(self):
        task = make_task("db_query", query="SELECT 1")
        result = self.agent.execute(task)
        assert result.success is True
        assert "Rows returned" in result.output

    def test_insert_and_select(self):
        self.agent.connection = sqlite3.connect(":memory:")
        self.agent.connection.execute("CREATE TABLE t (id INTEGER, name TEXT)")
        task_insert = make_task("db_query", query="INSERT INTO t VALUES (1, 'alice')")
        r1 = self.agent.execute(task_insert)
        assert r1.success is True

        task_select = make_task("db_query", query="SELECT * FROM t")
        r2 = self.agent.execute(task_select)
        assert r2.success is True
        assert "alice" in r2.output

    def test_query_no_query_returns_error(self):
        task = make_task("db_query", query="")
        result = self.agent.execute(task)
        assert result.success is False
        assert "No query provided" in result.error

    def test_invalid_sql_returns_error(self):
        task = make_task("db_query", query="SELECTBAD STUFF")
        result = self.agent.execute(task)
        assert result.success is False
        assert result.error is not None

    def test_multi_statement_query(self):
        self.agent.connection = sqlite3.connect(":memory:")
        query = "CREATE TABLE m (id INT); INSERT INTO m VALUES (99); SELECT * FROM m"
        task = make_task("db_query", query=query)
        result = self.agent.execute(task)
        assert result.success is True
        assert "Rows returned" in result.output

    def test_multi_statement_ends_with_non_select(self):
        self.agent.connection = sqlite3.connect(":memory:")
        query = "CREATE TABLE m2 (id INT); INSERT INTO m2 VALUES (1)"
        task = make_task("db_query", query=query)
        result = self.agent.execute(task)
        assert result.success is True
        assert "Rows affected" in result.output

    def test_raw_sql_task_uses_query_executor(self):
        task = make_task("db_raw_sql", query="SELECT 42")
        result = self.agent.execute(task)
        assert result.success is True


# ---------------------------------------------------------------------------
# execute() — migrate
# ---------------------------------------------------------------------------

class TestExecuteMigrate:
    def setup_method(self):
        self.agent = DatabaseAgent()

    def test_migrate_missing_dir(self, tmp_path):
        task = make_task("db_migrate", migration_path=str(tmp_path / "nonexistent"))
        result = self.agent.execute(task)
        assert result.success is False
        assert "does not exist" in result.error

    def test_migrate_empty_dir(self, tmp_path):
        task = make_task("db_migrate", migration_path=str(tmp_path))
        result = self.agent.execute(task)
        assert result.success is True
        assert "0 migration files" in result.output

    def test_migrate_counts_sql_files(self, tmp_path):
        (tmp_path / "001.sql").write_text("SELECT 1")
        (tmp_path / "002.sql").write_text("SELECT 2")
        (tmp_path / "ignore.txt").write_text("not sql")
        task = make_task("db_migrate", migration_path=str(tmp_path))
        result = self.agent.execute(task)
        assert result.success is True
        assert "2 migration files" in result.output


# ---------------------------------------------------------------------------
# execute() — schema
# ---------------------------------------------------------------------------

class TestExecuteSchema:
    def setup_method(self):
        self.agent = DatabaseAgent()
        self.agent.connection = sqlite3.connect(":memory:")
        self.agent.connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")

    def test_schema_all_tables(self):
        task = make_task("db_schema", table_name=None)
        result = self.agent.execute(task)
        assert result.success is True
        assert "users" in result.output

    def test_schema_specific_table(self):
        task = make_task("db_schema", table_name="users")
        result = self.agent.execute(task)
        assert result.success is True
        assert "users" in result.output
        assert "id" in result.output

    def test_schema_no_connection_uses_memory(self):
        self.agent.connection = None
        task = make_task("db_schema", table_name=None)
        result = self.agent.execute(task)
        assert result.success is True
        assert "0 tables" in result.output


# ---------------------------------------------------------------------------
# execute() — backup & restore
# ---------------------------------------------------------------------------

class TestExecuteBackupRestore:
    def setup_method(self):
        self.agent = DatabaseAgent()
        self.agent.connection = sqlite3.connect(":memory:")
        self.agent.connection.execute("CREATE TABLE data (v TEXT)")
        self.agent.connection.execute("INSERT INTO data VALUES ('hello')")
        self.agent.connection.commit()

    def test_backup_with_connection(self, tmp_path):
        backup_path = str(tmp_path / "backup.db")
        task = make_task("db_backup", backup_path=backup_path)
        result = self.agent.execute(task)
        assert result.success is True
        assert "backed up" in result.output
        assert Path(backup_path).exists()

    def test_backup_without_connection(self, tmp_path):
        self.agent.connection = None
        backup_path = str(tmp_path / "backup.sql")
        task = make_task("db_backup", backup_path=backup_path)
        result = self.agent.execute(task)
        assert result.success is True
        assert "prepared" in result.output

    def test_restore_missing_file(self):
        task = make_task("db_restore", backup_path="/nonexistent/backup.sql")
        result = self.agent.execute(task)
        assert result.success is False
        assert "does not exist" in result.error

    def test_restore_sql_file_with_connection(self, tmp_path):
        sql_file = tmp_path / "restore.sql"
        sql_file.write_text("CREATE TABLE restored (id INT);")
        task = make_task("db_restore", backup_path=str(sql_file))
        result = self.agent.execute(task)
        assert result.success is True
        assert "restored" in result.output

    def test_restore_sql_file_without_connection(self, tmp_path):
        sql_file = tmp_path / "restore.sql"
        sql_file.write_text("CREATE TABLE restored (id INT);")
        self.agent.connection = None
        task = make_task("db_restore", backup_path=str(sql_file))
        result = self.agent.execute(task)
        assert result.success is True
        assert "prepared" in result.output

    def test_restore_non_sql_file(self, tmp_path):
        other = tmp_path / "backup.bak"
        other.write_text("binary data")
        task = make_task("db_restore", backup_path=str(other))
        result = self.agent.execute(task)
        assert result.success is True


# ---------------------------------------------------------------------------
# execute() — unknown task id
# ---------------------------------------------------------------------------

class TestExecuteUnknownTask:
    def setup_method(self):
        self.agent = DatabaseAgent()

    def test_unknown_task_returns_error(self):
        task = make_task("db_unknown_xyz")
        result = self.agent.execute(task)
        assert result.success is False
        assert "Unknown task type" in result.error


# ---------------------------------------------------------------------------
# execute() — exception handling
# ---------------------------------------------------------------------------

class TestExecuteExceptionHandling:
    def setup_method(self):
        self.agent = DatabaseAgent()

    def test_execute_catches_unexpected_exception(self):
        task = make_task("db_connect", db_url="sqlite:///test.db")
        with patch.object(self.agent, "_execute_connect", side_effect=RuntimeError("boom")):
            result = self.agent.execute(task)
        assert result.success is False
        assert "boom" in result.error
