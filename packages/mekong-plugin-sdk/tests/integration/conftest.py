"""
Integration test fixtures for Mekong Plugin SDK.

Provides reusable fixtures for testing plugin lifecycle, commands, hooks,
events, config, storage, and other SDK components.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional
from unittest.mock import MagicMock

import pytest

from mekong_plugin_sdk import (
    MekongPlugin,
    PluginManifest,
    PluginContext,
    CommandRegistry,
    Command,
    Argument,
    Option,
    HookRegistry,
    HookPoint,
    EventBus,
    StandardEvent,
    PluginConfig,
    PluginLogger,
    LogLevel,
    PluginError,
    PluginErrorCode,
)
from mekong_plugin_sdk import (
    CommandResult,
    CommandContext,
    EventMetadata,
    EventPayload,
    Subscription,
)


# ==================== Test Plugins ====================

class MinimalTestPlugin(MekongPlugin):
    """A minimal plugin for basic testing."""

    def __init__(self, context: PluginContext):
        self.context = context
        self.initialized = False
        self.activated = False
        self.disposed = False
        self.commands_registered: List[str] = []
        self.hooks_registered: List[tuple] = []
        self.events_registered: List[tuple] = []

    @property
    def id(self) -> str:
        return "minimal-test-plugin"

    @property
    def name(self) -> str:
        return "Minimal Test Plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def engines(self) -> Dict[str, str]:
        return {"mekong": "^6.0.0"}

    def initialize(self, context: PluginContext) -> None:
        self.initialized = True
        self.context = context

    def activate(self) -> None:
        self.activated = True

    def register_commands(self, registry: CommandRegistry) -> None:
        # Register a simple test command
        registry.register(Command(
            name="test-command",
            description="A test command",
            handler=lambda ctx, args: {"result": "ok", "args": args},
            mcu_cost=1
        ))
        self.commands_registered.append("test-command")

    def register_hooks(self, hooks: HookRegistry) -> None:
        def test_handler(ctx, payload):
            pass
        hooks.register(HookPoint.AFTER_COMMAND, test_handler)
        self.hooks_registered.append((HookPoint.AFTER_COMMAND, test_handler))

    def register_events(self, event_bus: EventBus) -> None:
        def test_handler(payload, metadata):
            pass
        event_bus.on(StandardEvent.COMMAND_COMPLETED, test_handler)
        self.events_registered.append((StandardEvent.COMMAND_COMPLETED, test_handler))

    def dispose(self) -> None:
        self.disposed = True


class FullFeatureTestPlugin(MekongPlugin):
    """A full-featured test plugin with all features."""

    def __init__(self):
        self.context: Optional[PluginContext] = None
        self.initialized = False
        self.activated = False
        self.disposed = False

    @property
    def id(self) -> str:
        return "full-feature-test-plugin"

    @property
    def name(self) -> str:
        return "Full Feature Test Plugin"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def engines(self) -> Dict[str, str]:
        return {"mekong": "^6.0.0"}

    def initialize(self, context: PluginContext) -> None:
        self.initialized = True
        self.context = context

    def activate(self) -> None:
        self.activated = True

    def register_commands(self, registry: CommandRegistry) -> None:
        # Command with arguments and options
        def echo_handler(ctx: CommandContext, args: Dict[str, Any]) -> CommandResult:
            return CommandResult(
                success=True,
                output=f"Echo: {args.get('message', '')}",
                data={"args": args}
            )

        registry.register(Command(
            name="echo",
            description="Echo back a message",
            arguments=[
                Argument(name="message", type="string", description="Message to echo", required=True)
            ],
            options=[
                Option(name="repeat", alias="r", type="number", description="Repeat count", default=1)
            ],
            handler=echo_handler,
            mcu_cost=1
        ))

        # Command that raises an error
        def error_handler(ctx: CommandContext, args: Dict[str, Any]) -> CommandResult:
            raise PluginError(
                PluginErrorCode.COMMAND_HANDLER_ERROR,
                "Test error from command",
                self.id
            )

        registry.register(Command(
            name="error",
            description="Trigger an error",
            handler=error_handler,
            mcu_cost=0
        ))

    def register_hooks(self, hooks: HookRegistry) -> None:
        self.hook_calls: List[Dict[str, Any]] = []

        def before_cli_start_handler(ctx, payload):
            self.hook_calls.append({"point": "before_cli_start", "payload": payload})

        def after_command_handler(ctx, payload):
            self.hook_calls.append({"point": "after_command", "payload": payload})

        hooks.register(HookPoint.BEFORE_CLI_START, before_cli_start_handler, priority=10)
        hooks.register(HookPoint.AFTER_COMMAND, after_command_handler)

    def register_events(self, event_bus: EventBus) -> None:
        self.event_received: List[EventPayload] = []

        def event_handler(payload: EventPayload, metadata: EventMetadata):
            self.event_received.append(payload)

        event_bus.on(StandardEvent.COMMAND_STARTED, event_handler)
        event_bus.on(StandardEvent.COMMAND_COMPLETED, event_handler)

    def dispose(self) -> None:
        self.disposed = True


# ==================== Mock Services ====================

class MockStorage:
    """In-memory storage for testing."""

    def __init__(self):
        self._data: Dict[str, bytes] = {}

    def read_text(self, path: str) -> str:
        return self._data[path].decode('utf-8')

    def write_text(self, path: str, content: str) -> None:
        self._data[path] = content.encode('utf-8')

    def read_json(self, path: str) -> Dict[str, Any]:
        return json.loads(self.read_text(path))

    def write_json(self, path: str, data: Dict[str, Any]) -> None:
        self.write_text(path, json.dumps(data, indent=2))

    def exists(self, path: str) -> bool:
        return path in self._data

    def delete(self, path: str) -> None:
        del self._data[path]

    def list(self, dir_path: str) -> List[str]:
        prefix = dir_path + "/"
        return [k[len(prefix):] for k in self._data.keys() if k.startswith(prefix)]

    def stat(self, path: str):
        from mekong_plugin_sdk.types import FileStats
        from datetime import datetime
        return FileStats(
            size=len(self._data[path]),
            modified=datetime.now(),
            is_dir=False
        )

    def mkdir(self, dir_path: str, recursive: bool = False) -> None:
        # No-op for in-memory storage
        pass


class MockHttpClient:
    """Mock HTTP client for testing."""

    def __init__(self):
        self.responses: Dict[str, Any] = {}
        self.requests: List[Dict[str, Any]] = []

    def request(self, options: Dict[str, Any]) -> Dict[str, Any]:
        self.requests.append(options)
        url = options.get('url', '')
        if url in self.responses:
            return self.responses[url]
        return {"status": 404, "body": None}

    def get(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request({"method": "GET", "url": url, **(options or {})})

    def post(self, url: str, body: Any = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request({"method": "POST", "url": url, "body": body, **(options or {})})


# ==================== Pytest Fixtures ====================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def plugin_storage_dir(temp_dir: Path):
    """Provide a storage directory for plugin tests."""
    storage = temp_dir / "plugin_storage"
    storage.mkdir(parents=True)
    return storage


@pytest.fixture
def mock_config(plugin_storage_dir: Path):
    """Create a mock PluginConfig with temp storage."""
    return PluginConfig(
        plugin_id="test-plugin",
        config_dir=plugin_storage_dir,
        defaults={"key1": "default1", "key2": 42}
    )


@pytest.fixture
def mock_logger():
    """Create a PluginLogger for testing."""
    return PluginLogger("test-plugin", level=LogLevel.DEBUG)


@pytest.fixture
def mock_storage():
    """Create a mock storage instance."""
    return MockStorage()


@pytest.fixture
def mock_http():
    """Create a mock HTTP client."""
    return MockHttpClient()


@pytest.fixture
def minimal_plugin_class():
    """Provide the MinimalTestPlugin class."""
    return MinimalTestPlugin


@pytest.fixture
def full_plugin_class():
    """Provide the FullFeatureTestPlugin class."""
    return FullFeatureTestPlugin


@pytest.fixture
def sample_manifest() -> PluginManifest:
    """Create a sample plugin manifest."""
    return PluginManifest(
        id="sample-test-plugin",
        name="Sample Test Plugin",
        version="1.0.0",
        entrypoint="plugin:SamplePlugin",
        description="A sample plugin for testing",
        author="Test Author",
        license="MIT",
        permissions={"file": ["read"], "cli": ["command:register"]},
        mcu_cost=5
    )


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== Helper Functions ====================

def create_mock_context(
    plugin_id: str = "test-plugin",
    storage_dir: Optional[Path] = None,
    manifest: Optional[PluginManifest] = None
) -> MagicMock:
    """Create a mock PluginContext for testing."""
    if storage_dir is None:
        storage_dir = Path(tempfile.mkdtemp())

    if manifest is None:
        manifest = PluginManifest(
            id=plugin_id,
            name="Test Plugin",
            version="1.0.0",
            entrypoint="plugin:TestPlugin"
        )

    context = MagicMock(spec=PluginContext)
    context.id = plugin_id
    context.manifest = manifest
    context.storage_dir = storage_dir
    context.cache_dir = storage_dir / "cache"
    context.data_dir = storage_dir / "data"
    context.config = PluginConfig(plugin_id, storage_dir)
    context.logger = PluginLogger(plugin_id)
    context.events = EventBus()
    context.hooks = HookRegistry()
    context.commands = CommandRegistry()

    return context
