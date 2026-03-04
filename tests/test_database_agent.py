"""
Tests for DatabaseAgent in Mekong CLI
"""

import tempfile
import os

from src.agents.database_agent import DatabaseAgent
from src.core.agent_base import Task


class TestDatabaseAgent:
    """Test cases for DatabaseAgent"""

    def test_initialization(self):
        """Test DatabaseAgent initialization"""
        agent = DatabaseAgent()
        assert agent.name == "DatabaseAgent"
        assert agent.max_retries == 3

    def test_initialization_with_url(self):
        """Test DatabaseAgent initialization with URL"""
        db_url = "sqlite:///test.db"
        agent = DatabaseAgent(db_url=db_url)
        assert agent.db_url == db_url

    def test_plan_connect(self):
        """Test planning a connect command"""
        agent = DatabaseAgent()
        tasks = agent.plan("connect sqlite:///test.db")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_connect"
        assert task.description == "Connect to database: sqlite:///test.db"
        assert task.input == {"db_url": "sqlite:///test.db"}

    def test_plan_query(self):
        """Test planning a query command"""
        agent = DatabaseAgent()
        query = "SELECT * FROM users"
        tasks = agent.plan(f"query {query}")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_query"
        assert task.description == f"Execute query: {query}"
        assert task.input == {"query": query}

    def test_plan_migrate(self):
        """Test planning a migrate command"""
        agent = DatabaseAgent()
        migration_path = "./migrations"
        tasks = agent.plan(f"migrate {migration_path}")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_migrate"
        assert task.description == f"Run migrations from: {migration_path}"
        assert task.input == {"migration_path": migration_path}

    def test_plan_migrate_default(self):
        """Test planning a migrate command with default path"""
        agent = DatabaseAgent()
        tasks = agent.plan("migrate")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_migrate"
        assert task.description == "Run migrations from: ./migrations"
        assert task.input == {"migration_path": "./migrations"}

    def test_plan_schema(self):
        """Test planning a schema command"""
        agent = DatabaseAgent()
        table_name = "users"
        tasks = agent.plan(f"schema {table_name}")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_schema"
        assert task.description == f"Show schema for {table_name}"
        assert task.input == {"table_name": table_name}

    def test_plan_schema_all(self):
        """Test planning a schema command for all tables"""
        agent = DatabaseAgent()
        tasks = agent.plan("schema")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_schema"
        assert task.description == "Show schema"
        assert task.input == {"table_name": None}

    def test_plan_backup(self):
        """Test planning a backup command"""
        agent = DatabaseAgent()
        backup_path = "./backup.sql"
        tasks = agent.plan(f"backup {backup_path}")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_backup"
        assert task.description == f"Backup database to: {backup_path}"
        assert task.input == {"backup_path": backup_path}

    def test_plan_backup_default(self):
        """Test planning a backup command with default path"""
        agent = DatabaseAgent()
        tasks = agent.plan("backup")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_backup"
        assert task.description == "Backup database to: ./backup.sql"
        assert task.input == {"backup_path": "./backup.sql"}

    def test_plan_restore(self):
        """Test planning a restore command"""
        agent = DatabaseAgent()
        backup_path = "./backup.sql"
        tasks = agent.plan(f"restore {backup_path}")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_restore"
        assert task.description == f"Restore database from: {backup_path}"
        assert task.input == {"backup_path": backup_path}

    def test_plan_restore_default(self):
        """Test planning a restore command with default path"""
        agent = DatabaseAgent()
        tasks = agent.plan("restore")

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_restore"
        assert task.description == "Restore database from: ./backup.sql"
        assert task.input == {"backup_path": "./backup.sql"}

    def test_plan_raw_sql(self):
        """Test planning a raw SQL command"""
        agent = DatabaseAgent()
        query = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
        tasks = agent.plan(query)

        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "db_raw_sql"
        assert task.description == f"Execute raw SQL: {query}"
        assert task.input == {"query": query}

    def test_execute_connect(self):
        """Test executing a connect task"""
        agent = DatabaseAgent()

        task = Task(
            id="db_connect",
            description="Connect to test database",
            input={"db_url": "sqlite:///test.db"}
        )

        result = agent.execute(task)

        assert result.success is True
        assert result.task_id == "db_connect"
        assert result.error is None

    def test_execute_query_select(self):
        """Test executing a SELECT query"""
        agent = DatabaseAgent()

        # First create a table to query
        create_task = Task(
            id="db_query",
            description="Create test table",
            input={"query": "CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT); INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');"}
        )

        result = agent.execute(create_task)
        assert result.success is True

        # Now query the table
        query_task = Task(
            id="db_query",
            description="Execute SELECT query",
            input={"query": "SELECT * FROM users;"}
        )

        result = agent.execute(query_task)

        assert result.success is True
        assert result.task_id == "db_query"
        assert result.error is None
        assert "Rows returned:" in result.output

    def test_execute_query_modify(self):
        """Test executing a non-SELECT query"""
        agent = DatabaseAgent()

        # First create a table to insert into
        create_task = Task(
            id="db_query",
            description="Create test table",
            input={"query": "CREATE TABLE users (id INTEGER, name TEXT);"}
        )

        result = agent.execute(create_task)
        assert result.success is True

        # Now execute the insert
        task = Task(
            id="db_query",
            description="Execute INSERT query",
            input={"query": "INSERT INTO users (id, name) VALUES (3, 'Charlie');"}
        )

        result = agent.execute(task)

        assert result.success is True
        assert result.task_id == "db_query"
        assert result.error is None
        assert "Rows affected:" in result.output

    def test_execute_schema_table(self):
        """Test executing a schema task for a specific table"""
        agent = DatabaseAgent()

        # First create a table
        create_task = Task(
            id="db_query",
            description="Create test table",
            input={"query": "CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT NOT NULL);"}
        )

        result = agent.execute(create_task)
        assert result.success is True

        # Now get schema for the table
        schema_task = Task(
            id="db_schema",
            description="Get schema for test table",
            input={"table_name": "test_table"}
        )

        result = agent.execute(schema_task)

        assert result.success is True
        assert result.task_id == "db_schema"
        assert result.error is None
        assert "Schema for table" in result.output

    def test_execute_schema_all(self):
        """Test executing a schema task for all tables"""
        agent = DatabaseAgent()

        schema_task = Task(
            id="db_schema",
            description="Get all schema",
            input={"table_name": None}
        )

        result = agent.execute(schema_task)

        assert result.success is True
        assert result.task_id == "db_schema"
        assert result.error is None
        assert "Database contains" in result.output

    def test_execute_backup(self):
        """Test executing a backup task"""
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp_file:
            backup_path = tmp_file.name

        try:
            agent = DatabaseAgent()

            backup_task = Task(
                id="db_backup",
                description="Backup database",
                input={"backup_path": backup_path}
            )

            result = agent.execute(backup_task)

            assert result.success is True
            assert result.task_id == "db_backup"
            assert result.error is None

        finally:
            # Clean up
            if os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_execute_restore(self):
        """Test executing a restore task"""
        # Create a sample backup file
        with tempfile.NamedTemporaryFile(mode='w', suffix=".sql", delete=False) as tmp_file:
            tmp_file.write("-- Sample SQL backup\nCREATE TABLE users (id INTEGER, name TEXT);\nINSERT INTO users VALUES (1, 'Test');")
            backup_path = tmp_file.name

        try:
            agent = DatabaseAgent()

            restore_task = Task(
                id="db_restore",
                description="Restore database",
                input={"backup_path": backup_path}
            )

            result = agent.execute(restore_task)

            assert result.success is True
            assert result.task_id == "db_restore"
            assert result.error is None

        finally:
            # Clean up
            if os.path.exists(backup_path):
                os.unlink(backup_path)