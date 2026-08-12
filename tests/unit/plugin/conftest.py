"""Plugin Test Framework - Shared fixtures and utilities.

This module provides reusable fixtures for testing the plugin system.
Import this in plugin test files to get consistent test setup.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import plugin components
from src.core.plugin_loader import PluginLoader, DEFAULT_PLUGIN_DIR
from src.core.plugin_registry import PluginRegistry, PluginManifest, PluginStatus, PluginType
from src.core.plugin_validator import PluginValidator
from src.core.plugin_manager import PluginManager, PluginInfo


# ============================================================================
# Test Plugin Templates
# ============================================================================

BASIC_PLUGIN_TEMPLATE = '''
def register(registry):
    """Basic plugin registration."""
    pass
'''

VALID_PLUGIN_WITH_COMMANDS = '''
from typing import Dict, Any

def my_command_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Sample command handler."""
    return {"success": True, "output": "Hello from plugin!"}

def register(registry):
    """Register plugin commands."""
    registry.register("my-command", my_command_handler)
'''

PLUGIN_WITH_LIFECYCLE_HOOKS = '''
class MyPlugin:
    def __init__(self):
        self.loaded = False
        self.started = False

    def initialize(self, context):
        self.context = context
        self.loaded = True

    def register_commands(self, registry):
        registry.register("test-cmd", self.handle_test)

    def on_load(self, plugin_manager):
        self.started = True

    def on_unload(self):
        self.loaded = False

    def handle_test(self, args):
        return {"success": True}

    def dispose(self):
        pass

def create_plugin(context):
    return MyPlugin()

Plugin = MyPlugin
'''

MALICIOUS_PLUGIN_DANGEROUS_IMPORT = '''
import subprocess
import os

def register(registry):
    subprocess.run(["rm", "-rf", "/"])
'''

PLUGIN_WITH_SECRET = '''
API_KEY = "sk-secret1234567890abcdefghijklmnop"
def register(registry):
    pass
'''

PLUGIN_WITH_SYNTAX_ERROR = '''
def register(registry
    pass
'''

PLUGIN_WITHOUT_REGISTER = '''
def some_other_function():
    pass
'''

PLUGIN_WITH_INVALID_INTERFACE = '''
def register(registry):
    return "not a callable that accepts registry"
'''


# ============================================================================
# Fixtures: Temporary Directories
# ============================================================================

@pytest.fixture
def temp_plugin_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for plugin testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_plugins_structure(temp_plugin_dir: Path) -> Path:
    """Create a complete plugins directory structure with multiple test plugins."""
    plugins_dir = temp_plugin_dir / "plugins"
    plugins_dir.mkdir()

    # Create various test plugins
    (plugins_dir / "valid_basic.py").write_text(BASIC_PLUGIN_TEMPLATE)
    (plugins_dir / "valid_with_commands.py").write_text(VALID_PLUGIN_WITH_COMMANDS)
    (plugins_dir / "plugin_with_hooks.py").write_text(PLUGIN_WITH_LIFECYCLE_HOOKS)
    (plugins_dir / "_private_plugin.py").write_text(BASIC_PLUGIN_TEMPLATE)  # Should be skipped
    (plugins_dir / "test_fixture.py").write_text(BASIC_PLUGIN_TEMPLATE)  # Should be skipped
    (plugins_dir / "malicious_dangerous.py").write_text(MALICIOUS_PLUGIN_DANGEROUS_IMPORT)
    (plugins_dir / "plugin_with_secret.py").write_text(PLUGIN_WITH_SECRET)
    (plugins_dir / "syntax_error.py").write_text(PLUGIN_WITH_SYNTAX_ERROR)
    (plugins_dir / "no_register.py").write_text(PLUGIN_WITHOUT_REGISTER)

    return plugins_dir


@pytest.fixture
def single_valid_plugin(temp_plugin_dir: Path) -> Path:
    """Create a single valid plugin file."""
    plugin_file = temp_plugin_dir / "test_plugin.py"
    plugin_file.write_text(VALID_PLUGIN_WITH_COMMANDS)
    return plugin_file


@pytest.fixture
def temp_registry_index(temp_plugin_dir: Path) -> Path:
    """Create a temporary registry index file path."""
    return temp_plugin_dir / "plugin_registry.json"


# ============================================================================
# Fixtures: Component Instances
# ============================================================================

@pytest.fixture
def plugin_validator() -> PluginValidator:
    """Create a PluginValidator instance."""
    return PluginValidator()


@pytest.fixture
def plugin_loader() -> PluginLoader:
    """Create a PluginLoader instance."""
    return PluginLoader()


@pytest.fixture
def plugin_registry(temp_registry_index: Path) -> PluginRegistry:
    """Create a PluginRegistry with temporary index."""
    return PluginRegistry(index_path=temp_registry_index)


@pytest.fixture
def plugin_manager(temp_registry_index: Path) -> PluginManager:
    """Create a PluginManager with temporary registry."""
    return PluginManager(registry=PluginRegistry(index_path=temp_registry_index))


@pytest.fixture
def mock_agent_registry() -> MagicMock:
    """Create a mock agent registry for PluginLoader."""
    from unittest.mock import MagicMock
    return MagicMock()


# ============================================================================
# Fixtures: Sample Manifests
# ============================================================================

@pytest.fixture
def sample_manifest_dict() -> dict[str, Any]:
    """Return a sample plugin manifest dictionary."""
    return {
        "id": "com.example.test",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin for unit tests",
        "author": "Test Author",
        "entrypoint": "./plugin.py",
        "commands": [
            {
                "name": "test-command",
                "description": "Test command",
                "handler": "handle_test"
            }
        ]
    }


@pytest.fixture
def sample_full_manifest(temp_plugin_dir: Path) -> FullPluginManifest:
    """Create a sample FullPluginManifest with a real plugin file."""
    plugin_dir = temp_plugin_dir / "sample_plugin"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "plugin.py"
    plugin_file.write_text(VALID_PLUGIN_WITH_COMMANDS)

    manifest_path = plugin_dir / "plugin.json"
    manifest_path.write_text(json.dumps({
        "id": "com.example.sample",
        "name": "Sample Plugin",
        "version": "1.0.0",
        "description": "Sample plugin for testing",
        "entrypoint": "./plugin.py",
        "commands": [
            {
                "name": "sample-cmd",
                "description": "Sample command",
                "handler": "my_command_handler"
            }
        ]
    }))

    return FullPluginManifest.from_file(manifest_path)


# ============================================================================
# Fixtures: Mock HTTP responses for MarketplaceClient
# ============================================================================

@pytest.fixture
def mock_marketplace_responses() -> dict[str, Any]:
    """Return mock responses for marketplace API."""
    return {
        "health": {"status": "healthy"},
        "plugins": {
            "total": 2,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "plugins": [
                {
                    "name": "mekong-plugin-seo",
                    "version": "1.2.0",
                    "description": "SEO optimization plugin",
                    "author": "Mekong Team",
                    "plugin_type": "agent",
                    "downloads": 1500,
                    "rating": 4.5,
                    "rating_count": 100,
                    "tags": ["seo", "marketing"],
                    "min_mekong_version": "^6.0.0",
                    "dependencies": []
                },
                {
                    "name": "mekong-plugin-analytics",
                    "version": "2.0.0",
                    "description": "Analytics dashboard",
                    "author": "Data Team",
                    "plugin_type": "agent",
                    "downloads": 2500,
                    "rating": 4.8,
                    "rating_count": 200,
                    "tags": ["analytics", "dashboard"],
                    "min_mekong_version": "^6.0.0",
                    "dependencies": ["mekong-plugin-seo"]
                }
            ]
        },
        "plugin_detail": {
            "name": "mekong-plugin-seo",
            "version": "1.2.0",
            "description": "SEO optimization plugin",
            "author": "Mekong Team",
            "plugin_type": "agent",
            "downloads": 1500,
            "rating": 4.5,
            "rating_count": 100,
            "tags": ["seo", "marketing"],
            "repository_url": "https://github.com/mekong/plugin-seo",
            "documentation_url": "https://docs.mekong.dev/plugin-seo",
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-06-01T14:30:00Z",
            "license": "MIT",
            "min_mekong_version": "^6.0.0",
            "dependencies": []
        },
        "install_info": {
            "download_url": "https://marketplace.mekong.dev/download/plugin-seo",
            "checksum": "sha256:abc123def456",
            "version": "1.2.0"
        },
        "categories": [
            {"name": "Agents", "slug": "agents", "count": 45},
            {"name": "Providers", "slug": "providers", "count": 12}
        ],
        "tags": ["seo", "marketing", "analytics", "dashboard", "deployment"]
    }


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_plugin(
    plugin_dir: Path,
    name: str,
    content: str,
    with_manifest: bool = False,
    manifest_data: dict[str, Any] | None = None
) -> Path:
    """Create a test plugin file.

    Args:
        plugin_dir: Directory to create plugin in
        name: Plugin name (will be used as filename)
        content: Python code content
        with_manifest: Whether to create a plugin.json manifest
        manifest_data: Optional manifest dict (uses default if None)

    Returns:
        Path to created plugin file
    """
    plugin_file = plugin_dir / f"{name}.py"
    plugin_file.write_text(content)

    if with_manifest:
        manifest_path = plugin_dir / "plugin.json"
        if manifest_data is None:
            manifest_data = {
                "id": f"com.test.{name}",
                "name": name.title(),
                "version": "1.0.0",
                "description": f"Test plugin: {name}",
                "entrypoint": f"./{name}.py"
            }
        manifest_path.write_text(json.dumps(manifest_data))

    return plugin_file


def assert_plugin_valid(result: Any, message: str = "Plugin should be valid") -> None:
    """Assert that a validation result indicates a valid plugin."""
    assert result.is_valid, f"{message}: {result.errors}"


def assert_plugin_invalid(result: Any, expected_error: str | None = None) -> None:
    """Assert that a validation result indicates an invalid plugin."""
    assert not result.is_valid, "Plugin should be invalid"
    if expected_error:
        assert any(expected_error.lower() in err.lower() for err in result.errors), \
            f"Expected error containing '{expected_error}', got: {result.errors}"


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest for plugin tests."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection to add markers based on file path."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        if "security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.performance)
