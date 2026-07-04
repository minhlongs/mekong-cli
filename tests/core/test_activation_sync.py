"""Unit tests for src/core/activation_sync.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.activation_sync import ActivationSync


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sync(tmp_path: Path) -> "ActivationSync":
    """Create ActivationSync with mocked auth and tmp queue file."""
    from src.core.activation_sync import ActivationSync

    mock_auth = MagicMock()
    session = MagicMock()
    session.authenticated = False
    session.tenant = None
    mock_auth.get_session.return_value = session

    sync = ActivationSync(auth_client=mock_auth)
    sync._queue_file = tmp_path / "sync_queue.json"
    return sync


# ---------------------------------------------------------------------------
# _mask_key
# ---------------------------------------------------------------------------

class TestMaskKey:
    def test_long_key_masked(self):
        from src.core.activation_sync import ActivationSync
        sync = ActivationSync.__new__(ActivationSync)
        result = sync._mask_key("abcdefgh12345678")
        assert result.startswith("abcdefgh")
        assert result.endswith("5678")
        assert "..." in result

    def test_short_key_hidden(self):
        from src.core.activation_sync import ActivationSync
        sync = ActivationSync.__new__(ActivationSync)
        result = sync._mask_key("short")
        assert result == "(hidden)"

    def test_exactly_12_chars_hidden(self):
        from src.core.activation_sync import ActivationSync
        sync = ActivationSync.__new__(ActivationSync)
        result = sync._mask_key("123456789012")
        assert result == "(hidden)"

    def test_13_chars_masked(self):
        from src.core.activation_sync import ActivationSync
        sync = ActivationSync.__new__(ActivationSync)
        result = sync._mask_key("1234567890123")
        assert "..." in result


# ---------------------------------------------------------------------------
# _generate_idempotency_key
# ---------------------------------------------------------------------------

class TestGenerateIdempotencyKey:
    def test_returns_32_char_hex(self, tmp_path):
        sync = _make_sync(tmp_path)
        key = sync._generate_idempotency_key("tenant1", "agency1")
        assert len(key) == 32
        int(key, 16)  # raises ValueError if not hex

    def test_same_inputs_same_hour_returns_same_key(self, tmp_path):
        sync = _make_sync(tmp_path)
        k1 = sync._generate_idempotency_key("t", "a")
        k2 = sync._generate_idempotency_key("t", "a")
        assert k1 == k2

    def test_different_inputs_different_key(self, tmp_path):
        sync = _make_sync(tmp_path)
        k1 = sync._generate_idempotency_key("tenant1", "agency1")
        k2 = sync._generate_idempotency_key("tenant2", "agency2")
        assert k1 != k2


# ---------------------------------------------------------------------------
# _generate_signature
# ---------------------------------------------------------------------------

class TestGenerateSignature:
    def test_signature_starts_with_sha256(self, tmp_path):
        sync = _make_sync(tmp_path)
        sig = sync._generate_signature({"key": "value"})
        assert sig.startswith("sha256=")

    def test_same_event_same_signature(self, tmp_path):
        sync = _make_sync(tmp_path)
        event = {"a": 1, "b": 2}
        assert sync._generate_signature(event) == sync._generate_signature(event)

    def test_different_events_different_signatures(self, tmp_path):
        sync = _make_sync(tmp_path)
        assert sync._generate_signature({"a": 1}) != sync._generate_signature({"a": 2})


# ---------------------------------------------------------------------------
# _load_queue / _save_queue
# ---------------------------------------------------------------------------

class TestQueuePersistence:
    def test_load_queue_empty_when_no_file(self, tmp_path):
        sync = _make_sync(tmp_path)
        # queue file doesn't exist yet
        queue = sync._load_queue()
        assert queue == {"events": []}

    def test_save_and_load_roundtrip(self, tmp_path):
        sync = _make_sync(tmp_path)
        data = {"events": [{"event": {"x": 1}, "queued_at": "now", "retries": 0}]}
        sync._save_queue(data)
        loaded = sync._load_queue()
        assert loaded == data

    def test_load_returns_empty_on_corrupt_json(self, tmp_path):
        sync = _make_sync(tmp_path)
        sync._queue_file.write_text("NOT_JSON")
        queue = sync._load_queue()
        assert queue == {"events": []}


# ---------------------------------------------------------------------------
# _queue_event
# ---------------------------------------------------------------------------

class TestQueueEvent:
    def test_event_appended_to_queue(self, tmp_path):
        sync = _make_sync(tmp_path)
        event = {"event_type": "license_activated", "tenant_id": "t1"}
        sync._queue_event(event)
        queue = sync._load_queue()
        assert len(queue["events"]) == 1
        assert queue["events"][0]["event"] == event
        assert queue["events"][0]["retries"] == 0

    def test_multiple_events_accumulated(self, tmp_path):
        sync = _make_sync(tmp_path)
        sync._queue_event({"n": 1})
        sync._queue_event({"n": 2})
        queue = sync._load_queue()
        assert len(queue["events"]) == 2


# ---------------------------------------------------------------------------
# _send_event
# ---------------------------------------------------------------------------

class TestSendEvent:
    def test_returns_true_on_200(self, tmp_path):
        sync = _make_sync(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        sync._session.post = MagicMock(return_value=mock_resp)
        result = sync._send_event({"event_type": "test"})
        assert result is True

    def test_returns_true_on_201(self, tmp_path):
        sync = _make_sync(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        sync._session.post = MagicMock(return_value=mock_resp)
        assert sync._send_event({}) is True

    def test_returns_true_on_204(self, tmp_path):
        sync = _make_sync(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        sync._session.post = MagicMock(return_value=mock_resp)
        assert sync._send_event({}) is True

    def test_returns_false_on_4xx(self, tmp_path):
        sync = _make_sync(tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        sync._session.post = MagicMock(return_value=mock_resp)
        assert sync._send_event({}) is False

    def test_returns_false_on_network_error(self, tmp_path):
        import requests
        sync = _make_sync(tmp_path)
        sync._session.post = MagicMock(side_effect=requests.exceptions.ConnectionError("down"))
        assert sync._send_event({}) is False

    def test_adds_auth_header_when_session_authenticated(self, tmp_path):
        from src.core.activation_sync import ActivationSync
        mock_auth = MagicMock()
        session = MagicMock()
        session.authenticated = True
        session.tenant = MagicMock()
        session.tenant.license_key = "mk_testkey123"
        mock_auth.get_session.return_value = session

        sync = ActivationSync(auth_client=mock_auth)
        sync._queue_file = tmp_path / "q.json"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        sync._session.post = MagicMock(return_value=mock_resp)
        sync._send_event({"event_type": "test"})

        call_kwargs = sync._session.post.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert "mk_testkey123" in call_kwargs["headers"]["Authorization"]


# ---------------------------------------------------------------------------
# sync_activation
# ---------------------------------------------------------------------------

class TestSyncActivation:
    def test_returns_true_on_immediate_success(self, tmp_path):
        sync = _make_sync(tmp_path)
        sync._send_event = MagicMock(return_value=True)
        result = sync.sync_activation("t1", "a1", "pro")
        assert result is True

    def test_queues_on_failure_and_returns_true(self, tmp_path):
        sync = _make_sync(tmp_path)
        sync._send_event = MagicMock(return_value=False)
        result = sync.sync_activation("t1", "a1", "free")
        assert result is True  # queued = success for UX
        queue = sync._load_queue()
        assert len(queue["events"]) == 1

    def test_license_key_masked_in_event(self, tmp_path):
        sync = _make_sync(tmp_path)
        captured = {}

        def capture(event):
            captured.update(event)
            return True

        sync._send_event = capture
        sync.sync_activation("t1", "a1", "pro", license_key="abcdefgh12345678")
        assert "..." in captured.get("license_key", "")

    def test_no_license_key_sends_none(self, tmp_path):
        sync = _make_sync(tmp_path)
        captured = {}

        def capture(event):
            captured.update(event)
            return True

        sync._send_event = capture
        sync.sync_activation("t1", "a1", "pro")
        assert captured.get("license_key") is None

    def test_features_defaults_to_empty_list(self, tmp_path):
        sync = _make_sync(tmp_path)
        captured = {}

        def capture(event):
            captured.update(event)
            return True

        sync._send_event = capture
        sync.sync_activation("t1", "a1", "trial")
        assert captured["features"] == []

    def test_features_passed_correctly(self, tmp_path):
        sync = _make_sync(tmp_path)
        captured = {}

        def capture(event):
            captured.update(event)
            return True

        sync._send_event = capture
        sync.sync_activation("t1", "a1", "enterprise", features=["reporting", "api"])
        assert captured["features"] == ["reporting", "api"]

    def test_event_contains_required_fields(self, tmp_path):
        sync = _make_sync(tmp_path)
        captured = {}

        def capture(event):
            captured.update(event)
            return True

        sync._send_event = capture
        sync.sync_activation("tenant_x", "agency_y", "pro")
        for field in ("event_type", "tenant_id", "agency_id", "tier", "timestamp", "idempotency_key"):
            assert field in captured, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# process_queue
# ---------------------------------------------------------------------------

class TestProcessQueue:
    def test_empty_queue_returns_zero(self, tmp_path):
        sync = _make_sync(tmp_path)
        assert sync.process_queue() == 0

    def test_successful_events_processed_and_removed(self, tmp_path):
        sync = _make_sync(tmp_path)
        queue = {"events": [
            {"event": {"x": 1}, "queued_at": "now", "retries": 0},
            {"event": {"x": 2}, "queued_at": "now", "retries": 0},
        ]}
        sync._save_queue(queue)
        sync._send_event = MagicMock(return_value=True)
        count = sync.process_queue()
        assert count == 2
        remaining = sync._load_queue()
        assert remaining["events"] == []

    def test_failed_events_increment_retries(self, tmp_path):
        sync = _make_sync(tmp_path)
        queue = {"events": [
            {"event": {"x": 1}, "queued_at": "now", "retries": 0},
        ]}
        sync._save_queue(queue)
        sync._send_event = MagicMock(return_value=False)
        sync.process_queue()
        remaining = sync._load_queue()
        assert remaining["events"][0]["retries"] == 1

    def test_max_retries_exceeded_discards_event(self, tmp_path):
        sync = _make_sync(tmp_path)
        queue = {"events": [
            {"event": {"x": 1}, "queued_at": "now", "retries": 3},  # = MAX_RETRIES
        ]}
        sync._save_queue(queue)
        sync._send_event = MagicMock(return_value=False)
        count = sync.process_queue()
        remaining = sync._load_queue()
        assert remaining["events"] == []
        assert count == 0  # discarded, not processed

    def test_mixed_results(self, tmp_path):
        sync = _make_sync(tmp_path)
        queue = {"events": [
            {"event": {"id": "ok"}, "queued_at": "now", "retries": 0},
            {"event": {"id": "fail"}, "queued_at": "now", "retries": 0},
        ]}
        sync._save_queue(queue)

        results = [True, False]
        sync._send_event = MagicMock(side_effect=results)
        count = sync.process_queue()
        assert count == 1
        remaining = sync._load_queue()
        assert len(remaining["events"]) == 1
        assert remaining["events"][0]["retries"] == 1


# ---------------------------------------------------------------------------
# get_activation_sync singleton
# ---------------------------------------------------------------------------

class TestGetActivationSync:
    def test_returns_same_instance(self):
        import src.core.activation_sync as mod
        original = mod._sync_instance
        mod._sync_instance = None
        try:
            with patch("src.core.activation_sync.RaaSAuthClient"):
                inst1 = mod.get_activation_sync()
                inst2 = mod.get_activation_sync()
            assert inst1 is inst2
        finally:
            mod._sync_instance = original
