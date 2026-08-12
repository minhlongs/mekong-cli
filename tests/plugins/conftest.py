"""Pytest configuration for plugin system tests."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# Custom markers
def pytest_configure(config):
    """Configure pytest markers for plugin tests."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress/load tests"
    )
    config.addinivalue_line(
        "markers", "isolation: marks tests as security/isolation tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (use with --slow flag)"
    )


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests (stress/load tests)"
    )
    parser.addoption(
        "--benchmark",
        action="store_true",
        default=False,
        help="Run performance benchmarks"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests based on options."""
    skip_slow = pytest.mark.skip(reason="Need --slow option")
    skip_benchmark = pytest.mark.skip(reason="Need --benchmark option")

    if not config.getoption("--slow"):
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    if not config.getoption("--benchmark"):
        for item in items:
            if "performance" in item.keywords or "benchmark" in item.name.lower():
                item.add_marker(skip_benchmark)


@pytest.fixture
def temp_plugin_dir(tmp_path: Path) -> Path:
    """Create a temporary plugin directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    return plugin_dir


@pytest.fixture(autouse=True)
def disable_index_persistence(monkeypatch, request):
    """Disable index file persistence for plugin tests to avoid cross-test contamination.

    Tests that specifically need to test persistence can opt-out by using the
    @pytest.mark.use_persistence marker.
    """
    from src.core.plugin_registry import PluginRegistry

    # Skip if test is marked to use persistence
    if request.node.get_closest_marker("use_persistence"):
        return

    monkeypatch.setattr(PluginRegistry, "_load_index", lambda self: None)
    monkeypatch.setattr(PluginRegistry, "_save_index", lambda self: None)
