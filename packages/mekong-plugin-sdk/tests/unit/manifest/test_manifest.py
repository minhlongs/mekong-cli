"""Unit tests for mekong_plugin_sdk.manifest module."""

from mekong_plugin_sdk.manifest import PluginManifest, HookDefinition, EventDefinition


class TestPluginManifest:
    """Test suite for PluginManifest dataclass."""

    def test_manifest_creation_minimal(self):
        """Test PluginManifest with only required fields."""
        manifest = PluginManifest(
            id="com.example.plugin",
            name="Example Plugin",
            version="1.0.0"
        )
        assert manifest.id == "com.example.plugin"
        assert manifest.name == "Example Plugin"
        assert manifest.version == "1.0.0"
        assert manifest.description == ""
        assert manifest.author == ""
        assert manifest.license == "MIT"
        assert manifest.engines == {"mekong": "^6.0.0"}
        assert manifest.permissions == []
        assert manifest.mcu_cost == 1
        assert manifest.isolation == "none"
        assert manifest.config_schema == {}
        assert manifest.hooks == []
        assert manifest.events == []

    def test_manifest_creation_all_fields(self):
        """Test PluginManifest with all fields."""
        hooks = [
            HookDefinition(point="after_command", handler="on_after_command")
        ]
        events = [
            EventDefinition(event="plugin.loaded", handler="on_loaded")
        ]
        manifest = PluginManifest(
            id="com.example.full",
            name="Full Plugin",
            version="2.0.0",
            description="A fully-featured plugin",
            author="Developer Name",
            license="Apache-2.0",
            engines={"mekong": "^7.0.0"},
            permissions=["file:read", "network:outbound"],
            mcu_cost=5,
            isolation="process",
            config_schema={"type": "object", "properties": {"key": {"type": "string"}}},
            hooks=hooks,
            events=events
        )
        assert manifest.id == "com.example.full"
        assert manifest.description == "A fully-featured plugin"
        assert manifest.author == "Developer Name"
        assert manifest.license == "Apache-2.0"
        assert manifest.engines == {"mekong": "^7.0.0"}
        assert len(manifest.permissions) == 2
        assert manifest.mcu_cost == 5
        assert manifest.isolation == "process"
        assert len(manifest.config_schema) > 0
        assert len(manifest.hooks) == 1
        assert len(manifest.events) == 1

    def test_to_dict_minimal(self):
        """Test to_dict with minimal manifest."""
        manifest = PluginManifest(
            id="test.id",
            name="Test",
            version="0.1.0"
        )
        d = manifest.to_dict()
        assert d == {
            "id": "test.id",
            "name": "Test",
            "version": "0.1.0",
            "description": "",
            "author": "",
            "license": "MIT",
            "engines": {"mekong": "^6.0.0"},
            "permissions": [],
            "mcu_cost": 1,
            "isolation": "none"
        }

    def test_to_dict_with_extras(self):
        """Test to_dict includes config_schema, hooks, events when present."""
        manifest = PluginManifest(
            id="test.id",
            name="Test",
            version="1.0.0",
            config_schema={"type": "string"},
            hooks=[HookDefinition(point="before_command", handler="handler1")],
            events=[EventDefinition(event="command.started", handler="handler2")]
        )
        d = manifest.to_dict()
        assert "config_schema" in d
        assert "hooks" in d
        assert "events" in d
        assert len(d["hooks"]) == 1
        assert len(d["events"]) == 1

    def test_from_dict_minimal(self):
        """Test from_dict creates manifest from minimal dict."""
        data = {
            "id": "from.dict",
            "name": "From Dict",
            "version": "1.0.0"
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.id == "from.dict"
        assert manifest.name == "From Dict"
        assert manifest.version == "1.0.0"
        assert manifest.description == ""
        assert manifest.engines == {"mekong": "^6.0.0"}

    def test_from_dict_full(self):
        """Test from_dict with all fields."""
        data = {
            "id": "full.manifest",
            "name": "Full Manifest",
            "version": "3.0.0",
            "description": "Complete manifest test",
            "author": "Tester",
            "license": "BSD-3-Clause",
            "engines": {"mekong": "^6.0.0", "python": "^3.9"},
            "permissions": ["file:write", "shell:exec"],
            "mcu_cost": 10,
            "isolation": "container",
            "config_schema": {"type": "object"},
            "hooks": [
                {"point": "after_command", "handler": "on_after", "priority": 20}
            ],
            "events": [
                {"event": "error.occurred", "handler": "on_error"}
            ]
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.id == "full.manifest"
        assert manifest.description == "Complete manifest test"
        assert manifest.author == "Tester"
        assert manifest.engines == {"mekong": "^6.0.0", "python": "^3.9"}
        assert manifest.permissions == ["file:write", "shell:exec"]
        assert manifest.mcu_cost == 10
        assert manifest.isolation == "container"
        assert manifest.config_schema == {"type": "object"}
        assert len(manifest.hooks) == 1
        assert manifest.hooks[0].point == "after_command"
        assert manifest.hooks[0].handler == "on_after"
        assert manifest.hooks[0].priority == 20
        assert len(manifest.events) == 1
        assert manifest.events[0].event == "error.occurred"
        assert manifest.events[0].handler == "on_error"

    def test_from_dict_uses_defaults_for_missing_fields(self):
        """Test from_dict uses defaults for missing optional fields."""
        data = {
            "id": "minimal.data",
            "name": "Minimal",
            "version": "1.0.0"
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.description == ""
        assert manifest.license == "MIT"
        assert manifest.engines == {"mekong": "^6.0.0"}
        assert manifest.permissions == []
        assert manifest.mcu_cost == 1
        assert manifest.isolation == "none"
        assert manifest.config_schema == {}
        assert manifest.hooks == []
        assert manifest.events == []


class TestHookDefinition:
    """Test suite for HookDefinition dataclass."""

    def test_hook_definition_creation_required_only(self):
        """Test HookDefinition with required fields only."""
        hook_def = HookDefinition(
            point="before_command",
            handler="my_handler"
        )
        assert hook_def.point == "before_command"
        assert hook_def.handler == "my_handler"
        assert hook_def.priority == 50

    def test_hook_definition_creation_custom_priority(self):
        """Test HookDefinition with custom priority."""
        hook_def = HookDefinition(
            point="after_command",
            handler="handler_func",
            priority=10
        )
        assert hook_def.priority == 10

    def test_hook_definition_to_dict(self):
        """Test HookDefinition serialization."""
        hook_def = HookDefinition(
            point="on_shutdown",
            handler="cleanup",
            priority=100
        )
        d = hook_def.to_dict()
        assert d == {
            "point": "on_shutdown",
            "handler": "cleanup",
            "priority": 100
        }

    def test_hook_definition_from_dict(self):
        """Test HookDefinition deserialization."""
        data = {
            "point": "before_plan",
            "handler": "plan_start",
            "priority": 5
        }
        hook_def = HookDefinition.from_dict(data)
        assert hook_def.point == "before_plan"
        assert hook_def.handler == "plan_start"
        assert hook_def.priority == 5

    def test_hook_definition_from_dict_default_priority(self):
        """Test HookDefinition from_dict uses default priority if missing."""
        data = {
            "point": "after_execute",
            "handler": "exec_done"
        }
        hook_def = HookDefinition.from_dict(data)
        assert hook_def.priority == 50


class TestEventDefinition:
    """Test suite for EventDefinition dataclass."""

    def test_event_definition_creation(self):
        """Test EventDefinition creation."""
        event_def = EventDefinition(
            event="command.completed",
            handler="on_command_done"
        )
        assert event_def.event == "command.completed"
        assert event_def.handler == "on_command_done"

    def test_event_definition_to_dict(self):
        """Test EventDefinition serialization."""
        event_def = EventDefinition(
            event="plugin.loaded",
            handler="on_load"
        )
        d = event_def.to_dict()
        assert d == {"event": "plugin.loaded", "handler": "on_load"}

    def test_event_definition_from_dict(self):
        """Test EventDefinition deserialization."""
        data = {"event": "error.occurred", "handler": "log_error"}
        event_def = EventDefinition.from_dict(data)
        assert event_def.event == "error.occurred"
        assert event_def.handler == "log_error"
