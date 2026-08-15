"""Zalo OA Automation Rules Engine."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import time as _time_of_day
from typing import Any, Callable

from .client import ZaloOAClient
from .models import (
    AutomationAction,
    AutomationRule,
    ZaloTextMessage,
    ZaloWebhookPayload,
)
from .templates import ZaloTemplateEngine

logger = logging.getLogger(__name__)


@dataclass
class AutomationContext:
    """Context passed to automation actions."""

    user_id: str
    message_text: str
    payload: ZaloWebhookPayload
    client: ZaloOAClient | None = None
    template_engine: ZaloTemplateEngine | None = None
    user_tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


class ZaloAutomationEngine:
    """Rules engine for keyword-based automation."""

    def __init__(
        self,
        client: ZaloOAClient | None = None,
        template_engine: ZaloTemplateEngine | None = None,
    ):
        """Initialize automation engine.

        Args:
            client: Zalo OA client for sending messages
            template_engine: Template engine for rendering messages
        """
        self.client = client
        self.template_engine = template_engine or ZaloTemplateEngine()
        self.rules: list[AutomationRule] = []
        self._custom_actions: dict[str, Callable] = {}
        self._custom_conditions: dict[str, Callable] = {}
        # In-memory message timestamps per user for the message_count condition.
        self._message_history: dict[str, list[float]] = {}

        # Built-in action handlers
        self._action_handlers = {
            "send_message": self._action_send_message,
            "send_template": self._action_send_template,
            "tag_user": self._action_tag_user,
            "call_webhook": self._action_call_webhook,
            "delay": self._action_delay,
        }

        # Built-in condition evaluators
        self._condition_evaluators = {
            "user_tag": self._condition_user_tag,
            "time_range": self._condition_time_range,
            "user_locale": self._condition_user_locale,
            "message_count": self._condition_message_count,
        }

    def add_rule(self, rule: AutomationRule) -> None:
        """Add an automation rule.

        Args:
            rule: AutomationRule to add
        """
        # Remove existing rule with same ID
        self.rules = [r for r in self.rules if r.id != rule.id]
        self.rules.append(rule)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID.

        Args:
            rule_id: Rule ID to remove

        Returns:
            True if rule was removed
        """
        original_len = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        return len(self.rules) < original_len

    def get_rule(self, rule_id: str) -> AutomationRule | None:
        """Get rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def list_rules(self, enabled_only: bool = True) -> list[AutomationRule]:
        """List all rules.

        Args:
            enabled_only: If True, only return enabled rules

        Returns:
            List of rules
        """
        rules = self.rules
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules

    def register_custom_action(self, name: str, handler: Callable) -> None:
        """Register a custom action handler.

        Args:
            name: Action name
            handler: Async function(context, params) -> None
        """
        self._custom_actions[name] = handler

    def register_custom_condition(self, name: str, evaluator: Callable) -> None:
        """Register a custom condition evaluator.

        Args:
            name: Condition name
            evaluator: Function(context, params) -> bool
        """
        self._custom_conditions[name] = evaluator

    async def execute_rules(
        self,
        user_id: str,
        message_text: str,
        payload: ZaloWebhookPayload,
    ) -> list[str]:
        """Execute matching automation rules for a message.

        Args:
            user_id: Zalo user ID
            message_text: Incoming message text
            payload: Full webhook payload

        Returns:
            List of executed rule IDs
        """
        if not self.client:
            logger.warning("No Zalo client configured, skipping automation")
            return []

        context = AutomationContext(
            user_id=user_id,
            message_text=message_text,
            payload=payload,
            client=self.client,
            template_engine=self.template_engine,
        )

        executed = []

        # Record this message for the message_count condition
        self._record_message(user_id)

        for rule in self.rules:
            if not rule.enabled:
                continue

            if self._matches_rule(rule, message_text, context):
                if await self._check_conditions(rule, context):
                    await self._execute_actions(rule, context)
                    executed.append(rule.id)
                    logger.info(f"Executed automation rule: {rule.id} for user {user_id}")

                    # Stop at first match if rule has high priority (optional)
                    # For now, execute all matching rules

        return executed

    def _record_message(self, user_id: str) -> None:
        """Record a message timestamp for the message_count condition."""
        now = time.time()
        timestamps = self._message_history.setdefault(user_id, [])
        timestamps.append(now)
        # Prune entries older than the largest window we support (1 hour)
        cutoff = now - 3600
        self._message_history[user_id] = [ts for ts in timestamps if ts >= cutoff]

    def _matches_rule(self, rule: AutomationRule, message_text: str, context: AutomationContext) -> bool:
        """Check if message matches rule keywords."""
        message_lower = message_text.lower()

        for keyword in rule.keywords:
            keyword_lower = keyword.lower()

            if rule.match_type == "exact":
                if message_lower == keyword_lower:
                    return True
            elif rule.match_type == "contains":
                if keyword_lower in message_lower:
                    return True
            elif rule.match_type == "regex":
                try:
                    if re.search(keyword, message_text, re.IGNORECASE):
                        return True
                except re.error:
                    logger.error(f"Invalid regex in rule {rule.id}: {keyword}")

        return False

    async def _check_conditions(self, rule: AutomationRule, context: AutomationContext) -> bool:
        """Check all conditions for a rule."""
        for condition in rule.conditions:
            evaluator = self._condition_evaluators.get(condition.type)
            if condition.type in self._custom_conditions:
                evaluator = self._custom_conditions[condition.type]

            if not evaluator:
                logger.warning(f"Unknown condition type: {condition.type}")
                return False

            try:
                if asyncio.iscoroutinefunction(evaluator):
                    result = await evaluator(context, condition.params)
                else:
                    result = evaluator(context, condition.params)

                if not result:
                    return False
            except Exception as e:
                logger.error(f"Condition evaluation error: {e}")
                return False

        return True

    async def _execute_actions(self, rule: AutomationRule, context: AutomationContext) -> None:
        """Execute all actions for a rule."""
        for action in rule.actions:
            handler = self._action_handlers.get(action.type)
            if action.type in self._custom_actions:
                handler = self._custom_actions[action.type]

            if not handler:
                logger.warning(f"Unknown action type: {action.type}")
                continue

            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(context, action.params)
                else:
                    result = handler(context, action.params)
                    if asyncio.iscoroutine(result):
                        await result
            except Exception as e:
                logger.error(f"Action execution error ({action.type}): {e}")

    # Built-in action handlers
    async def _action_send_message(self, context: AutomationContext, params: dict[str, Any]) -> None:
        """Send a text message."""
        if not context.client:
            return

        content = params.get("content", "")

        # Support template variables in content
        if context.template_engine and "{" in content:
            try:
                content = context.template_engine.env.from_string(content).render(
                    name=context.payload.sender.name if context.payload.sender else "bạn",
                    **context.metadata,
                )
            except Exception:
                pass

        message = ZaloTextMessage(recipient_id=context.user_id, content=content)
        await context.client.send_message(message)

    async def _action_send_template(self, context: AutomationContext, params: dict[str, Any]) -> None:
        """Send a templated message."""
        if not context.client or not context.template_engine:
            return

        template_name = params.get("template", "")
        locale = params.get("locale", "vi_VN")
        message_type = params.get("message_type", "text")

        # Merge params with context metadata
        template_params = {**context.metadata, **params.get("template_params", {})}

        message = context.template_engine.render_message(
            template_name=template_name,
            recipient_id=context.user_id,
            locale=locale,
            message_type=message_type,
            **template_params,
        )

        await context.client.send_message(message)

    async def _action_tag_user(self, context: AutomationContext, params: dict[str, Any]) -> None:
        """Tag user (store in context for later use)."""
        tag = params.get("tag", "")
        if tag:
            context.user_tags.add(tag)
            context.metadata[f"tag_{tag}"] = True

    async def _action_call_webhook(self, context: AutomationContext, params: dict[str, Any]) -> None:
        """Call external webhook."""
        url = params.get("url", "")
        method = params.get("method", "POST")
        payload = params.get("payload", {})

        if not url:
            return

        import httpx

        async with httpx.AsyncClient() as client:
            await client.request(
                method,
                url,
                json={**payload, "user_id": context.user_id, "message": context.message_text},
                timeout=10.0,
            )

    async def _action_delay(self, context: AutomationContext, params: dict[str, Any]) -> None:
        """Delay execution."""
        seconds = params.get("seconds", 1)
        await asyncio.sleep(min(seconds, 60))  # Cap at 60 seconds

    # Built-in condition evaluators
    def _condition_user_tag(self, context: AutomationContext, params: dict[str, Any]) -> bool:
        """Check if user has tag."""
        required_tag = params.get("tag", "")
        return required_tag in context.user_tags

    def _condition_time_range(self, context: AutomationContext, params: dict[str, Any]) -> bool:
        """Check if current time is within range."""
        start_str = params.get("start", "00:00")
        end_str = params.get("end", "23:59")
        timezone_str = params.get("timezone", "Asia/Ho_Chi_Minh")

        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo

            tz = ZoneInfo(timezone_str)
            now = datetime.now(tz).time()
            start = _time_of_day.fromisoformat(start_str)
            end = _time_of_day.fromisoformat(end_str)

            if start <= end:
                return start <= now <= end
            else:  # Overnight range
                return now >= start or now <= end
        except Exception:
            return True  # Fail open

    def _condition_user_locale(self, context: AutomationContext, params: dict[str, Any]) -> bool:
        """Check user locale."""
        required_locale = str(params.get("locale", "vi_VN"))
        user_locale = context.payload.sender.locale if context.payload.sender else "vi_VN"
        return user_locale == required_locale

    def _condition_message_count(self, context: AutomationContext, params: dict[str, Any]) -> bool:
        """Check message count in time window.

        Uses in-memory per-user message history recorded by ``execute_rules``.
        For production multi-instance deployments, swap in a KV/Redis-backed
        implementation via ``register_custom_condition``.
        """
        max_count = int(params.get("max", 10))
        window_seconds = int(params.get("window", 3600))

        now = time.time()
        timestamps = self._message_history.get(context.user_id, [])
        recent = [ts for ts in timestamps if now - ts <= window_seconds]
        return len(recent) <= max_count


# Pre-built common rules
def create_common_rules() -> list[AutomationRule]:
    """Create common automation rules."""
    return [
        AutomationRule(
            id="welcome_new_follower",
            name="Welcome New Follower",
            keywords=["follow", "theo dõi"],
            match_type="contains",
            priority=100,
            enabled=True,
            actions=[
                AutomationAction(
                    type="send_template",
                    params={"template": "welcome", "locale": "vi_VN"},
                ),
            ],
        ),
        AutomationRule(
            id="help_command",
            name="Help Command",
            keywords=["help", "hướng dẫn", "huong dan", "menu"],
            match_type="contains",
            priority=90,
            enabled=True,
            actions=[
                AutomationAction(
                    type="send_template",
                    params={"template": "help", "locale": "vi_VN"},
                ),
            ],
        ),
        AutomationRule(
            id="fallback_response",
            name="Fallback Response",
            keywords=["*"],  # Match all (will be checked last due to low priority)
            match_type="contains",
            priority=1,
            enabled=True,
            actions=[
                AutomationAction(
                    type="send_template",
                    params={"template": "fallback", "locale": "vi_VN"},
                ),
            ],
        ),
    ]