"""Tests for Notifier EventBus subscriber."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.notifier import Notifier, NotifyConfig
from src.core.event_bus import EventBus, Event
import src.core.event_bus as _eb
from tests.conftest import _real_event_type as EventType


class TestNotifyConfig(unittest.TestCase):
    """Test NotifyConfig dataclass."""

    def test_defaults(self):
        """Default config has 3 event types."""
        c = NotifyConfig()
        self.assertIn("goal_completed", c.events)
        self.assertIn("job_started", c.events)
        self.assertIn("job_completed", c.events)
        self.assertTrue(c.enabled)


class TestNotifier(unittest.TestCase):
    """Test Notifier subscribe/unsubscribe and event handling."""

    def setUp(self):
        self.bus = EventBus()
        _eb._default_bus = self.bus

    def tearDown(self):
        _eb._default_bus = None

    def test_subscribe_registers_events(self):
        """Subscribing increases subscriber count."""
        notifier = Notifier(bot=None)
        initial = self.bus.subscriber_count
        notifier.subscribe(self.bus)
        self.assertGreater(self.bus.subscriber_count, initial)

    def test_unsubscribe_removes(self):
        """Unsubscribing decreases subscriber count."""
        notifier = Notifier(bot=None)
        notifier.subscribe(self.bus)
        count_after_sub = self.bus.subscriber_count
        notifier.unsubscribe(self.bus)
        self.assertLess(self.bus.subscriber_count, count_after_sub)

    def test_should_notify_configured_event(self):
        """goal_completed is in default config -> True."""
        notifier = Notifier(bot=None)
        self.assertTrue(notifier._should_notify(EventType.GOAL_COMPLETED))

    def test_should_notify_unconfigured_event(self):
        """Events not in config -> False."""
        notifier = Notifier(bot=None)
        self.assertFalse(notifier._should_notify(EventType.GOAL_STARTED))

    def test_on_event_no_bot(self):
        """Silently skips when no bot."""
        notifier = Notifier(bot=None)
        event = Event(type=EventType.GOAL_COMPLETED, data={"goal": "test"})
        # Should not raise
        notifier.on_event(event)

    def test_on_event_bot_not_running(self):
        """Skips when bot exists but not running."""
        mock_bot = MagicMock()
        mock_bot.is_running.return_value = False
        notifier = Notifier(bot=mock_bot)
        event = Event(type=EventType.GOAL_COMPLETED, data={"goal": "test"})
        notifier.on_event(event)
        # send_notification should NOT be called
        mock_bot.send_notification.assert_not_called()

    def test_on_event_unconfigured_skips(self):
        """Skips when event type not configured."""
        mock_bot = MagicMock()
        mock_bot.is_running.return_value = True
        notifier = Notifier(bot=mock_bot)
        event = Event(type=EventType.GOAL_STARTED, data={"goal": "test"})
        notifier.on_event(event)
        mock_bot.send_notification.assert_not_called()

    def test_on_event_send_notification_success(self):
        """Dispatches notification to bot when configured and running."""
        mock_bot = MagicMock()
        mock_bot.is_running.return_value = True
        mock_bot.config.chat_ids = [101, 102]

        notifier = Notifier(bot=mock_bot)
        event = Event(
            type=EventType.GOAL_COMPLETED,
            data={"goal": "deploy app", "status": "failed"},
        )

        with patch("asyncio.run_coroutine_threadsafe") as mock_run_coro:
            with patch("asyncio.get_event_loop") as mock_loop:
                notifier.on_event(event)
                self.assertEqual(mock_run_coro.call_count, 2)
                mock_loop.assert_called()

    def test_on_event_send_notification_exception_handled(self):
        """Logs warning if asyncio.run_coroutine_threadsafe raises."""
        mock_bot = MagicMock()
        mock_bot.is_running.return_value = True
        mock_bot.config.chat_ids = [101]

        notifier = Notifier(bot=mock_bot)
        event = Event(
            type=EventType.GOAL_COMPLETED,
            data={"goal": "test", "status": "success"},
        )

        with patch("asyncio.run_coroutine_threadsafe", side_effect=RuntimeError("event loop error")):
            # Must not crash
            notifier.on_event(event)

    def test_format_notification_goal_completed(self):
        """Formats goal_completed event."""
        notifier = Notifier(bot=None)
        event = Event(
            type=EventType.GOAL_COMPLETED,
            data={"goal": "deploy app", "status": "success"},
        )
        text = notifier._format_notification(event)
        self.assertIn("deploy app", text)
        self.assertIn("success", text)
        self.assertTrue(text.startswith("✅"))

    def test_format_notification_goal_completed_failed_status(self):
        """Formats failed goal_completed event with red cross."""
        notifier = Notifier(bot=None)
        event = Event(
            type=EventType.GOAL_COMPLETED,
            data={"goal": "deploy app", "status": "failed"},
        )
        text = notifier._format_notification(event)
        self.assertIn("deploy app", text)
        self.assertIn("failed", text)
        self.assertTrue(text.startswith("❌"))

    def test_format_notification_job_started(self):
        """Formats job_started event."""
        notifier = Notifier(bot=None)
        event = Event(
            type=EventType.JOB_STARTED,
            data={"name": "daily-backup"},
        )
        text = notifier._format_notification(event)
        self.assertIn("daily-backup", text)
        self.assertIn("started", text.lower())

    def test_format_notification_job_completed(self):
        """Formats job_completed event."""
        notifier = Notifier(bot=None)
        event = Event(
            type=EventType.JOB_COMPLETED,
            data={"name": "nightly-scan"},
        )
        text = notifier._format_notification(event)
        self.assertIn("nightly-scan", text)

    def test_format_notification_fallback_event(self):
        """Formats generic event not matching predefined formats."""
        notifier = Notifier(bot=None)
        event = Event(
            type=EventType.STEP_FAILED,
            data={"error": "timeout"},
        )
        text = notifier._format_notification(event)
        self.assertEqual(text, f"🔔 Event: {EventType.STEP_FAILED.value}")

    def test_load_config_defaults(self):
        """Default config when no file exists."""
        notifier = Notifier(bot=None)
        self.assertIsInstance(notifier.config, NotifyConfig)
        self.assertEqual(len(notifier.config.events), 3)

    def test_load_config_from_yaml(self):
        """Loads custom yaml file when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "notify.yaml"
            config_file.write_text("events:\n  - job_started\nenabled: false\n")

            with patch.object(Notifier, "CONFIG_PATH", str(config_file)):
                notifier = Notifier(bot=None)
                self.assertEqual(notifier.config.events, ["job_started"])
                self.assertFalse(notifier.config.enabled)

    def test_load_config_yaml_error_fallback(self):
        """Falls back to defaults if yaml parsing fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "notify.yaml"
            config_file.write_text(": invalid : yaml : [")

            with patch.object(Notifier, "CONFIG_PATH", str(config_file)):
                notifier = Notifier(bot=None)
                self.assertEqual(len(notifier.config.events), 3)
                self.assertTrue(notifier.config.enabled)

    def test_disabled_config_skips(self):
        """Disabled config skips notification."""
        notifier = Notifier(bot=None)
        notifier.config.enabled = False
        mock_bot = MagicMock()
        mock_bot.is_running.return_value = True
        notifier.bot = mock_bot
        event = Event(type=EventType.GOAL_COMPLETED, data={})
        notifier.on_event(event)
        mock_bot.send_notification.assert_not_called()


if __name__ == "__main__":
    unittest.main()
