# Plugin Test Framework Design

**Last Updated**: 2026-06-22  
**Status**: Design Document  
**Purpose**: Comprehensive testing strategy for Mekong CLI plugin system

---

## Overview

This document defines the testing framework for the Mekong CLI plugin system. The framework provides utilities, fixtures, base classes, and test suites covering all test categories: unit, integration, E2E, performance, and security.

---

## 1. Test Directory Structure

```
tests/
├── unit/
│   ├── plugin_manager/
│   │   ├── test_plugin_manager.py
│   │   ├── test_plugin_registry.py
│   │   ├── test_plugin_validator.py
│   │   └── test_plugin_loader.py
│   ├── plugins/
│   │   ├── test_plugin_manifest.py
│   │   ├── test_plugin_isolation.py
│   │   └── test_plugin_sandbox.py
│   ├── marketplace/
│   │   ├── test_plugin_marketplace.py
│   │   ├── test_plugin_discovery.py
│   │   └── test_plugin_installer.py
│   └── fixtures/
│       ├── conftest.py
│       ├── factories.py
│       └── mocks.py
├── integration/
│   ├── test_plugin_lifecycle.py
│   ├── test_plugin_dependencies.py
│   ├── test_plugin_updates.py
│   └── test_plugin_uninstall.py
├── e2e/
│   ├── test_plugin_marketplace_flow.py
│   ├── test_plugin_install_uninstall.py
│   ├── test_plugin_developer_workflow.py
│   └── test_plugin_user_journey.py
├── performance/
│   ├── test_plugin_load_time.py
│   ├── test_plugin_memory_footprint.py
│   ├── test_concurrent_plugin_ops.py
│   └── benchmarks/
│       ├── benchmark_plugin_loading.py
│       ├── benchmark_plugin_execution.py
│       └── regression_suite.py
├── security/
│   ├── test_plugin_isolation_boundaries.py
│   ├── test_plugin_permissions.py
│   ├── test_plugin_sandbox_escape.py
│   ├── test_plugin_resource_limits.py
│   └── test_plugin_code_injection.py
├── isolation/
│   ├── test_plugin_sandboxing.py
│   ├── test_filesystem_isolation.py
│   ├── test_network_isolation.py
│   └── test_process_isolation.py
└── conftest.py (root-level shared fixtures)
```

---

## 2. Test Fixtures and Factories

### 2.1 Core Fixtures (`tests/unit/fixtures/conftest.py`)

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from mekong.plugin import PluginManager, PluginRegistry, PluginValidator
from tests.fixtures.factories import PluginFactory

@pytest.fixture
def temp_dir():
    """Create and cleanup temporary directory"""
    tmpdir = tempfile.mkdtemp(prefix="mekong-test-")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

@pytest.fixture
def plugin_factory():
    """Factory for creating test plugins"""
    return PluginFactory()

@pytest.fixture
def valid_plugin_manifest(plugin_factory):
    """Generate a valid plugin manifest"""
    return plugin_factory.create_valid()

@pytest.fixture
def invalid_plugin_manifest(plugin_factory):
    """Generate an invalid plugin manifest"""
    return plugin_factory.create_invalid()

@pytest.fixture
def plugin_registry(temp_dir):
    """Create isolated plugin registry"""
    config_path = temp_dir / "registry.json"
    return PluginRegistry(config_path)

@pytest.fixture
def plugin_validator():
    """Create plugin validator instance"""
    return PluginValidator()

@pytest.fixture
def plugin_manager(temp_dir, plugin_registry):
    """Create isolated plugin manager"""
    plugins_dir = temp_dir / "plugins"
    plugins_dir.mkdir()
    return PluginManager(plugins_dir, plugin_registry)
```

### 2.2 Plugin Factory (`tests/unit/fixtures/factories.py`)

```python
from typing import Dict, Any
from pathlib import Path
import json

class PluginFactory:
    """Factory for generating test plugin manifests and structures"""
    
    def create_valid(self, **overrides) -> Dict[str, Any]:
        """Create a valid plugin manifest with optional overrides"""
        manifest = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test plugin for unit testing",
            "author": "Test Author",
            "license": "MIT",
            "entrypoint": "plugin.py",
            "commands": [
                {
                    "name": "test",
                    "description": "Test command",
                    "handler": "handle_test"
                }
            ],
            "dependencies": [],
            "permissions": {
                "network": False,
                "filesystem": "sandboxed",
                "subprocess": False
            }
        }
        manifest.update(overrides)
        return manifest
    
    def create_invalid(self, error_type: str = "missing_name") -> Dict[str, Any]:
        """Create an invalid plugin manifest"""
        if error_type == "missing_name":
            return {"version": "1.0.0"}  # Missing required 'name'
        elif error_type == "invalid_version":
            return {"name": "test", "version": "invalid"}
        elif error_type == "malformed_json":
            return "not a dict"
        return self.create_valid()
    
    def create_plugin_structure(
        self, 
        path: Path, 
        manifest: Dict[str, Any]
    ) -> Path:
        """Create full plugin directory structure"""
        plugin_dir = path / manifest["name"]
        plugin_dir.mkdir()
        
        # Write manifest
        manifest_path = plugin_dir / "mekong-plugin.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Write entrypoint
        entrypoint = plugin_dir / manifest["entrypoint"]
        entrypoint.write_text(self._generate_plugin_code(manifest))
        
        return plugin_dir
    
    def _generate_plugin_code(self, manifest: Dict[str, Any]) -> str:
        """Generate Python code for plugin entrypoint"""
        commands = "\n        ".join([
            f'self.register_command("{cmd["name"]}", self.{cmd["handler"]})'
            for cmd in manifest.get("commands", [])
        ])
        
        return f'''"""
Plugin: {manifest['name']}
Version: {manifest['version']}
"""

from mekong.plugin import Plugin

class {self._to_camel_case(manifest['name'])}Plugin(Plugin):
    def __init__(self):
        super().__init__(
            name="{manifest['name']}",
            version="{manifest['version']}"
        )
        {commands}
    
    def initialize(self):
        """Plugin initialization"""
        pass
    
    def cleanup(self):
        """Plugin cleanup"""
        pass
'''
    
    def _to_camel_case(self, name: str) -> str:
        """Convert kebab-case to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('-'))
```

---

## 3. Unit Tests Coverage Plan

### 3.1 PluginManager Tests

**File**: `tests/unit/plugin_manager/test_plugin_manager.py`

**Coverage Targets**:
- Plugin discovery and loading: 100%
- Plugin lifecycle (initialize, start, stop): 100%
- Error handling and recovery: 95%+
- Command registration: 100%

**Test Cases**:
```python
class TestPluginManager:
    def test_load_plugin_from_directory(self, plugin_manager, plugin_factory):
        """Test loading valid plugin from directory"""
        
    def test_reject_invalid_plugin(self, plugin_manager, invalid_plugin_manifest):
        """Test rejection of invalid manifest"""
        
    def test_plugin_duplicate_name(self, plugin_manager, plugin_factory):
        """Test handling of duplicate plugin names"""
        
    def test_plugin_dependency_resolution(self, plugin_manager, plugin_factory):
        """Test dependency resolution order"""
        
    def test_plugin_lifecycle_start_stop(self, plugin_manager):
        """Test plugin start/stop cycle"""
        
    def test_plugin_command_invocation(self, plugin_manager, plugin_factory):
        """Test command execution through plugin"""
```

### 3.2 PluginRegistry Tests

**File**: `tests/unit/plugin_manager/test_plugin_registry.py`

**Coverage Targets**:
- CRUD operations: 100%
- Serialization/deserialization: 100%
- Concurrent access: 95%+

**Test Cases**:
```python
class TestPluginRegistry:
    def test_register_plugin(self, plugin_registry, valid_plugin_manifest):
        """Test plugin registration"""
        
    def test_unregister_plugin(self, plugin_registry):
        """Test plugin removal"""
        
    def test_list_plugins(self, plugin_registry):
        """Test listing all registered plugins"""
        
    def test_get_plugin_by_name(self, plugin_registry):
        """Test plugin lookup by name"""
        
    def test_persistence_across_restart(self, temp_dir):
        """Test registry persists to disk"""
        
    def test_concurrent_registration(self, plugin_registry):
        """Test thread-safe registration"""
```

### 3.3 PluginValidator Tests

**File**: `tests/unit/plugin_manager/test_plugin_validator.py`

**Coverage Targets**:
- Schema validation: 100%
- Permission checking: 100%
- Security policy enforcement: 95%+

**Test Cases**:
```python
class TestPluginValidator:
    def test_validate_valid_manifest(self, plugin_validator, valid_plugin_manifest):
        """Test validation of valid manifest"""
        
    def test_reject_missing_required_fields(self, plugin_validator):
        """Test rejection of missing required fields"""
        
    def test_validate_semantic_version(self, plugin_validator):
        """Test version string validation"""
        
    def test_validate_permissions(self, plugin_validator):
        """Test permission scope validation"""
        
    def test_validate_command_names(self, plugin_validator):
        """Test command name uniqueness and format"""
        
    def test_dependency_version_constraints(self, plugin_validator):
        """Test semantic version constraint checking"""
```

### 3.4 Plugin Loader Tests

**File**: `tests/unit/plugin_manager/test_plugin_loader.py`

**Coverage Targets**:
- Dynamic module loading: 95%+
- Sandbox isolation: 100%
- Error recovery: 95%+

**Test Cases**:
```python
class TestPluginLoader:
    def test_load_plugin_module(self, temp_dir, plugin_factory):
        """Test dynamic Python module loading"""
        
    def test_load_plugin_with_dependencies(self, plugin_factory):
        """Test loading with unresolved dependencies"""
        
    def test_sandbox_file_access(self, plugin_loader):
        """Test filesystem sandboxing"""
        
    def test_sandbox_network_access(self, plugin_loader):
        """Test network access restrictions"""
        
    def test_sandbox_subprocess_restrictions(self, plugin_loader):
        """Test subprocess execution limits"""
```

---

## 4. Integration Tests

**File**: `tests/integration/test_plugin_lifecycle.py`

```python
class TestPluginLifecycle:
    """Test plugin lifecycle across multiple operations"""
    
    def test_install_enable_disable_uninstall(self, plugin_manager, plugin_factory):
        """Complete plugin lifecycle"""
        # 1. Install
        # 2. Enable
        # 3. Verify commands available
        # 4. Disable
        # 5. Verify commands hidden
        # 6. Uninstall
        # 7. Verify cleanup
    
    def test_plugin_version_upgrade(self, plugin_manager, plugin_factory):
        """Test plugin upgrade from v1 to v2"""
        
    def test_plugin_dependency_changes(self, plugin_manager):
        """Test dependency graph updates"""
        
    def test_plugin_configuration_migration(self, plugin_manager):
        """Test config migration between versions"""
```

---

## 5. E2E Tests

**File**: `tests/e2e/test_plugin_marketplace_flow.py`

```python
class TestPluginMarketplaceE2E:
    """End-to-end marketplace workflows"""
    
    def test_user_discovers_installs_plugin(self, cli_runner):
        """User discovers, installs, and uses a marketplace plugin"""
        # 1. Search marketplace
        # 2. View plugin details
        # 3. Install plugin
        # 4. Verify command available
        # 5. Execute command
        # 6. Uninstall
    
    def test_developer_publishes_plugin(self, cli_runner, temp_dir):
        """Developer uploads plugin to marketplace"""
        # 1. Create plugin structure
        # 2. Validate locally
        # 3. Submit to marketplace
        # 4. Verify appears in search
        # 5. Other user installs
```

---

## 6. Performance Tests

**File**: `tests/performance/test_plugin_load_time.py`

```python
class TestPluginLoadPerformance:
    """Performance benchmarks for plugin operations"""
    
    def test_plugin_load_scales_linearly(self, benchmark):
        """Test that loading N plugins takes O(N) time"""
        # Generate 10, 50, 100 plugins
        # Measure load time
        # Assert linear scaling
    
    def test_plugin_command_invocation_latency(self, benchmark):
        """Test command execution latency stays < 100ms"""
        # p99 latency target: 100ms
        
    def test_memory_footprint_per_plugin(self):
        """Test memory overhead stays bounded (~10MB/plugin)"""
```

---

## 7. Security Tests

**File**: `tests/security/test_plugin_isolation_boundaries.py`

```python
class TestPluginIsolation:
    """Verify plugin sandbox boundaries"""
    
    def test_plugin_cannot_access_parent_filesystem(self, plugin_loader):
        """Plugin cannot read/write outside sandbox"""
        
    def test_plugin_cannot_spawn_unbounded_processes(self, plugin_loader):
        """Process creation limited by policy"""
        
    def test_plugin_network_access_denied_by_default(self, plugin_loader):
        """Network access requires explicit permission"""
        
    def test_plugin_code_injection_prevented(self, plugin_loader):
        """Ensure no arbitrary code execution"""
```

---

## 8. Mock Implementations

**File**: `tests/unit/fixtures/mocks.py`

```python
from unittest.mock import MagicMock, patch
from mekong.plugin import Plugin

class MockPlugin(Plugin):
    """Lightweight mock plugin for unit tests"""
    def __init__(self, name="mock", commands=None):
        super().__init__(name=name, version="1.0.0")
        if commands:
            for cmd in commands:
                self.register_command(cmd, lambda: None)
    
    def initialize(self):
        pass
    
    def cleanup(self):
        pass

class MockPluginManager:
    """Mock plugin manager for isolation tests"""
    def __init__(self):
        self.plugins = {}
        self.commands = {}
    
    def register(self, plugin):
        self.plugins[plugin.name] = plugin
        self.commands.update(plugin.commands)
```

---

## 9. CI/CD Integration

**File**: `.github/workflows/plugin-tests.yml` (summary)

```yaml
name: Plugin Tests
on: [push, pull_request]
jobs:
  unit:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -e .[test]
      - name: Run unit tests
        run: pytest tests/unit --cov=mekong.plugin --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
  
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest tests/integration --timeout=30
  
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker-compose up -d
      - name: Run e2e tests
        run: pytest tests/e2e --timeout=60
  
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run benchmarks
        run: pytest tests/performance --benchmark-only
  
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security tests
        run: pytest tests/security
```

---

## 10. Coverage Requirements

| Component | Unit | Integration | E2E | Security |
|-----------|------|-------------|-----|----------|
| PluginManager | 95% | 90% | 85% | 90% |
| PluginRegistry | 95% | 90% | 80% | 85% |
| PluginValidator | 95% | 85% | 80% | 95% |
| PluginLoader | 90% | 85% | 80% | 100% |
| Marketplace | 90% | 85% | 85% | 85% |

**Overall Target**: 90% code coverage minimum

---

## 11. Test Utilities

**File**: `tests/plugins/utils.py`

```python
def wait_for_plugin_event(event_name: str, timeout: float = 5.0):
    """Wait for plugin event with timeout"""
    pass

def assert_command_exists(cli, command_name: str):
    """Assert CLI has command registered"""
    pass

def capture_plugin_logs(plugin_name: str):
    """Capture plugin-specific log output"""
    pass
```

---

This design provides comprehensive testing coverage for all plugin system components with clear separation of concerns, proper fixtures, and CI/CD integration.
