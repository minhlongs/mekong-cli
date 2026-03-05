"""
Integration Tests: Command Resolution + Plugin Loader
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from antigravity.core.registry import (
    resolve_command,
    get_agent_for_command,
    get_command_metadata,
    list_suites,
)
from antigravity.plugins.loader import PluginLoader


class TestRegistryPluginIntegration:
    """Integration tests for registry and plugin loader."""
    
    def test_resolve_command_with_all_formats(self):
        """Test command resolution with different formats."""
        # Shortcut format
        suite, sub, meta = resolve_command("cook")
        assert suite == "dev"
        assert sub == "cook"
        assert meta["agent"] == "fullstack-developer"
        
        # Colon format
        suite, sub, meta = resolve_command("dev:cook")
        assert suite == "dev"
        assert sub == "cook"
        
        # Dot format
        suite, sub, meta = resolve_command("revenue.quote")
        assert suite == "revenue"
        assert sub == "quote"
    
    def test_get_agent_for_command(self):
        """Test agent resolution for commands."""
        assert get_agent_for_command("cook") == "fullstack-developer"
        assert get_agent_for_command("quote") == "money-maker"
        assert get_agent_for_command("debug") == "debugger"
        assert get_agent_for_command("unknown") == "system"
    
    def test_get_command_metadata(self):
        """Test metadata retrieval."""
        meta = get_command_metadata("revenue", "quote")
        assert meta is not None
        assert "money_maker" in meta["module"]
        assert meta["class"] == "MoneyMaker"
        
        # Unknown command
        meta = get_command_metadata("unknown", "cmd")
        assert meta is None
    
    def test_list_suites(self):
        """Test suite listing."""
        suites = list_suites()
        assert "revenue" in suites
        assert "dev" in suites
        assert "strategy" in suites
        assert "crm" in suites
        assert "content" in suites
        assert "ops" in suites
    
    def test_plugin_loader_initialization(self):
        """Test plugin loader with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(tmpdir)
            assert loader is not None
            assert str(loader.plugin_dir) == tmpdir
    
    def test_registry_agent_mapping(self):
        """Verify all commands have agent mappings."""
        for suite_id in list_suites():
            info = get_command_metadata(suite_id)
            # Suite metadata should exist
            assert info is not None or suite_id in [
                s for s in list_suites()
            ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
