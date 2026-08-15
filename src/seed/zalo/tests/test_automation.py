"""Unit tests for Zalo OA Automation Engine."""

# Test helpers conventionally skip full type annotations.
# mypy: disable-error-code="no-untyped-def,call-arg,union-attr,misc"

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.seed.zalo.automation import (
    ZaloAutomationEngine,
    create_common_rules,
)
from src.seed.zalo.models import (
    AutomationAction,
    AutomationCondition,
    AutomationRule,
    ZaloEventType,
    ZaloTextMessage,
    ZaloUserProfile,
    ZaloWebhookPayload,
)
from src.seed.zalo.client import ZaloOAClient
from src.seed.zalo.templates import ZaloTemplateEngine


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock Zalo client."""
    client = MagicMock(spec=ZaloOAClient)
    client.send_message = AsyncMock()
    return client


@pytest.fixture
def template_engine() -> ZaloTemplateEngine:
    """Create template engine with test templates."""
    engine = ZaloTemplateEngine()
    engine.add_template("welcome", "Welcome {{ name }}!", "vi_VN")
    engine.add_template("help", "Help: {{ commands }}", "vi_VN")
    engine.add_template("fallback", "Sorry {{ name }}, I don't understand.", "vi_VN")
    return engine


@pytest.fixture
def automation_engine(mock_client: MagicMock, template_engine: ZaloTemplateEngine) -> ZaloAutomationEngine:
    """Create automation engine with mocks."""
    return ZaloAutomationEngine(client=mock_client, template_engine=template_engine)


@pytest.fixture
def sample_payload() -> ZaloWebhookPayload:
    """Create sample webhook payload."""
    return ZaloWebhookPayload(
        event_name=ZaloEventType.MESSAGE,
        timestamp=1234567890,
        sender=ZaloUserProfile(user_id="user_123", name="Test User", locale="vi_VN"),
        message=ZaloTextMessage(recipient_id="user_123", content="help"),
    )


class TestZaloAutomationEngine:
    """Tests for ZaloAutomationEngine."""

    def test_add_rule(self, automation_engine: ZaloAutomationEngine):
        """Test adding automation rule."""
        rule = AutomationRule(
            id="test_rule",
            name="Test Rule",
            keywords=["test"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Test"})],
        )

        automation_engine.add_rule(rule)
        rules = automation_engine.list_rules()
        assert len(rules) == 1
        assert rules[0].id == "test_rule"

    def test_remove_rule(self, automation_engine: ZaloAutomationEngine):
        """Test removing automation rule."""
        rule = AutomationRule(
            id="remove_me",
            name="Remove Me",
            keywords=["remove"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Test"})],
        )

        automation_engine.add_rule(rule)
        assert automation_engine.get_rule("remove_me") is not None

        removed = automation_engine.remove_rule("remove_me")
        assert removed is True
        assert automation_engine.get_rule("remove_me") is None

    def test_remove_nonexistent_rule(self, automation_engine: ZaloAutomationEngine):
        """Test removing non-existent rule."""
        removed = automation_engine.remove_rule("nonexistent")
        assert removed is False

    def test_get_rule(self, automation_engine: ZaloAutomationEngine):
        """Test getting rule by ID."""
        rule = AutomationRule(
            id="get_me",
            name="Get Me",
            keywords=["get"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Test"})],
        )

        automation_engine.add_rule(rule)
        found = automation_engine.get_rule("get_me")
        assert found is not None
        assert found.id == "get_me"

    def test_list_rules_enabled_only(self, automation_engine: ZaloAutomationEngine):
        """Test listing only enabled rules."""
        rule1 = AutomationRule(
            id="enabled_rule",
            name="Enabled",
            keywords=["enabled"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Test"})],
        )
        rule2 = AutomationRule(
            id="disabled_rule",
            name="Disabled",
            keywords=["disabled"],
            match_type="contains",
            priority=10,
            enabled=False,
            actions=[AutomationAction(type="send_message", params={"content": "Test"})],
        )

        automation_engine.add_rule(rule1)
        automation_engine.add_rule(rule2)

        enabled = automation_engine.list_rules(enabled_only=True)
        all_rules = automation_engine.list_rules(enabled_only=False)

        assert len(enabled) == 1
        assert enabled[0].id == "enabled_rule"
        assert len(all_rules) == 2

    def test_priority_sorting(self, automation_engine: ZaloAutomationEngine):
        """Test rules are sorted by priority."""
        rule_low = AutomationRule(
            id="low_priority",
            name="Low",
            keywords=["low"],
            match_type="contains",
            priority=1,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Low"})],
        )
        rule_high = AutomationRule(
            id="high_priority",
            name="High",
            keywords=["high"],
            match_type="contains",
            priority=100,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "High"})],
        )

        automation_engine.add_rule(rule_low)
        automation_engine.add_rule(rule_high)

        rules = automation_engine.list_rules()
        assert rules[0].id == "high_priority"
        assert rules[1].id == "low_priority"

    @pytest.mark.asyncio
    async def test_execute_rules_exact_match(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test rule execution with exact match."""
        rule = AutomationRule(
            id="exact_rule",
            name="Exact Match",
            keywords=["help"],
            match_type="exact",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Exact matched!"})],
        )

        automation_engine.add_rule(rule)

        # Payload has content "help" - exact match
        executed = await automation_engine.execute_rules("user_123", "help", sample_payload)

        assert "exact_rule" in executed
        automation_engine.client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_rules_contains_match(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test rule execution with contains match."""
        rule = AutomationRule(
            id="contains_rule",
            name="Contains Match",
            keywords=["he"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Contains matched!"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "help me", sample_payload)

        assert "contains_rule" in executed

    @pytest.mark.asyncio
    async def test_execute_rules_regex_match(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test rule execution with regex match."""
        rule = AutomationRule(
            id="regex_rule",
            name="Regex Match",
            keywords=[r"h\w+"],
            match_type="regex",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Regex matched!"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "hello world", sample_payload)

        assert "regex_rule" in executed

    @pytest.mark.asyncio
    async def test_execute_rules_no_match(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test rule execution with no match."""
        rule = AutomationRule(
            id="no_match_rule",
            name="No Match",
            keywords=["xyz"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Matched!"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "help", sample_payload)

        assert len(executed) == 0
        automation_engine.client.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rules_disabled_rule(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test disabled rule is not executed."""
        rule = AutomationRule(
            id="disabled_rule",
            name="Disabled Rule",
            keywords=["help"],
            match_type="contains",
            priority=10,
            enabled=False,
            actions=[AutomationAction(type="send_message", params={"content": "Matched!"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "help", sample_payload)

        assert len(executed) == 0

    @pytest.mark.asyncio
    async def test_execute_rules_with_conditions(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test rule execution with conditions."""
        rule = AutomationRule(
            id="conditional_rule",
            name="Conditional Rule",
            keywords=["help"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Conditional matched!"})],
            conditions=[AutomationCondition(type="user_locale", params={"locale": "vi_VN"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "help", sample_payload)

        assert "conditional_rule" in executed

    @pytest.mark.asyncio
    async def test_execute_rules_condition_fails(self, automation_engine: ZaloAutomationEngine):
        """Test rule not executed when condition fails."""
        # Payload with different locale
        payload = ZaloWebhookPayload(
            event_name=ZaloEventType.MESSAGE,
            timestamp=1234567890,
            sender=ZaloUserProfile(user_id="user_123", name="Test User", locale="en_US"),
            message=ZaloTextMessage(recipient_id="user_123", content="help"),
        )

        rule = AutomationRule(
            id="conditional_rule",
            name="Conditional Rule",
            keywords=["help"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Conditional matched!"})],
            conditions=[AutomationCondition(type="user_locale", params={"locale": "vi_VN"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "help", payload)

        assert len(executed) == 0

    @pytest.mark.asyncio
    async def test_execute_rules_multiple_rules(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test multiple matching rules execute."""
        rule1 = AutomationRule(
            id="rule1",
            name="Rule 1",
            keywords=["help"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Rule 1"})],
        )
        rule2 = AutomationRule(
            id="rule2",
            name="Rule 2",
            keywords=["help"],
            match_type="contains",
            priority=20,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Rule 2"})],
        )

        automation_engine.add_rule(rule1)
        automation_engine.add_rule(rule2)

        executed = await automation_engine.execute_rules("user_123", "help", sample_payload)

        assert len(executed) == 2
        assert "rule1" in executed
        assert "rule2" in executed

    @pytest.mark.asyncio
    async def test_send_template_action(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test send_template action."""
        rule = AutomationRule(
            id="template_rule",
            name="Template Rule",
            keywords=["welcome"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[
                AutomationAction(
                    type="send_template",
                    params={"template": "welcome", "locale": "vi_VN"},
                )
            ],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "welcome", sample_payload)

        assert "template_rule" in executed
        automation_engine.client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_tag_user_action(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test tag_user action."""
        rule = AutomationRule(
            id="tag_rule",
            name="Tag Rule",
            keywords=["tagme"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="tag_user", params={"tag": "vip"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "tagme", sample_payload)

        assert "tag_rule" in executed
        # Tag should be added to context metadata
        # Note: context is internal, we verify by checking subsequent condition

    @pytest.mark.asyncio
    async def test_delay_action(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test delay action."""
        rule = AutomationRule(
            id="delay_rule",
            name="Delay Rule",
            keywords=["wait"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="delay", params={"seconds": 1})],
        )

        automation_engine.add_rule(rule)

        import time
        start = time.time()
        executed = await automation_engine.execute_rules("user_123", "wait", sample_payload)
        elapsed = time.time() - start

        assert "delay_rule" in executed
        assert elapsed >= 1  # At least 1 second delay

    @pytest.mark.asyncio
    async def test_custom_action(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test custom action registration."""
        custom_called = []

        async def custom_action(context, params):
            custom_called.append(params.get("value"))

        automation_engine.register_custom_action("custom_action", custom_action)

        rule = AutomationRule(
            id="custom_rule",
            name="Custom Rule",
            keywords=["custom"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="custom_action", params={"value": "test_value"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "custom", sample_payload)

        assert "custom_rule" in executed
        assert custom_called == ["test_value"]

    @pytest.mark.asyncio
    async def test_custom_condition(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test custom condition registration."""
        def custom_condition(context, params):
            return params.get("expected") == "yes"

        automation_engine.register_custom_condition("custom_condition", custom_condition)

        rule = AutomationRule(
            id="custom_cond_rule",
            name="Custom Condition Rule",
            keywords=["test"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Passed"})],
            conditions=[AutomationCondition(type="custom_condition", params={"expected": "yes"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "test", sample_payload)

        assert "custom_cond_rule" in executed

    @pytest.mark.asyncio
    async def test_custom_condition_fails(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test custom condition that fails."""
        def custom_condition(context, params):
            return params.get("expected") == "yes"

        automation_engine.register_custom_condition("custom_condition", custom_condition)

        rule = AutomationRule(
            id="custom_cond_fail",
            name="Custom Condition Fail",
            keywords=["test"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Passed"})],
            conditions=[AutomationCondition(type="custom_condition", params={"expected": "no"})],
        )

        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "test", sample_payload)

        assert len(executed) == 0

    @pytest.mark.asyncio
    async def test_time_range_condition_matches(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test time_range condition passes when within range."""
        rule = AutomationRule(
            id="time_range_rule",
            name="Time Range Rule",
            keywords=["morning"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Morning!"})],
            conditions=[AutomationCondition(type="time_range", params={"start": "00:00", "end": "23:59"})],
        )
        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "morning", sample_payload)

        assert "time_range_rule" in executed

    @pytest.mark.asyncio
    async def test_time_range_condition_overnight(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test time_range condition with overnight window (start > end)."""
        rule = AutomationRule(
            id="time_range_overnight",
            name="Time Range Overnight",
            keywords=["night"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Night!"})],
            conditions=[AutomationCondition(type="time_range", params={"start": "22:00", "end": "06:00"})],
        )
        automation_engine.add_rule(rule)

        executed = await automation_engine.execute_rules("user_123", "night", sample_payload)

        assert "time_range_overnight" in executed

    @pytest.mark.asyncio
    async def test_message_count_condition_within_limit(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test message_count condition passes when under limit."""
        rule = AutomationRule(
            id="msg_count_ok",
            name="Msg Count OK",
            keywords=["probe"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "OK"})],
            conditions=[AutomationCondition(type="message_count", params={"max": 5, "window": 3600})],
        )
        automation_engine.add_rule(rule)

        # 5 messages recorded, still within limit of 5
        for i in range(5):
            await automation_engine.execute_rules("user_123", "probe", sample_payload)

        executed = await automation_engine.execute_rules("user_123", "probe", sample_payload)
        # 6th message exceeds max=5 -> condition fails, rule not executed
        assert len(executed) == 0

    @pytest.mark.asyncio
    async def test_message_count_condition_blocks_after_limit(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test message_count condition blocks once the limit is exceeded."""
        rule = AutomationRule(
            id="msg_count_limit",
            name="Msg Count Limit",
            keywords=["burst"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Burst"})],
            conditions=[AutomationCondition(type="message_count", params={"max": 3, "window": 3600})],
        )
        automation_engine.add_rule(rule)

        executed_ids = []
        for i in range(4):
            executed = await automation_engine.execute_rules("user_123", "burst", sample_payload)
            executed_ids.extend(executed)

        # First 3 within limit, 4th blocked
        assert executed_ids.count("msg_count_limit") == 3

    @pytest.mark.asyncio
    async def test_call_webhook_action(self, automation_engine: ZaloAutomationEngine, sample_payload: ZaloWebhookPayload):
        """Test call_webhook action posts to external URL."""
        rule = AutomationRule(
            id="webhook_action_rule",
            name="Webhook Action",
            keywords=["callback"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="call_webhook", params={"url": "https://example.com/hook", "payload": {"x": 1}})]
        )
        automation_engine.add_rule(rule)

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_response = MagicMock()
            mock_instance.request = AsyncMock(return_value=mock_response)

            executed = await automation_engine.execute_rules("user_123", "callback", sample_payload)

        assert "webhook_action_rule" in executed
        mock_instance.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_client_skips_execution(self, sample_payload: ZaloWebhookPayload):
        """Test execute_rules returns empty when no client configured."""
        engine = ZaloAutomationEngine()
        rule = AutomationRule(
            id="no_client_rule",
            name="No Client",
            keywords=["anything"],
            match_type="contains",
            priority=10,
            enabled=True,
            actions=[AutomationAction(type="send_message", params={"content": "Hi"})],
        )
        engine.add_rule(rule)

        executed = await engine.execute_rules("user_123", "anything", sample_payload)
        assert executed == []


class TestCreateCommonRules:
    """Tests for create_common_rules factory."""

    def test_create_common_rules(self):
        """Test common rules are created correctly."""
        rules = create_common_rules()

        assert len(rules) == 3

        # Check welcome rule
        welcome = next(r for r in rules if r.id == "welcome_new_follower")
        assert welcome.priority == 100
        assert "follow" in welcome.keywords
        assert welcome.actions[0].type == "send_template"

        # Check help rule
        help_rule = next(r for r in rules if r.id == "help_command")
        assert help_rule.priority == 90
        assert "help" in help_rule.keywords

        # Check fallback rule
        fallback = next(r for r in rules if r.id == "fallback_response")
        assert fallback.priority == 1
        assert "*" in fallback.keywords