"""Tests for RaaS SSE infrastructure.

Covers:
- SSEManager register/unregister/push (queue lifecycle, drop-on-full)
- EventBusAdapter translation of internal events to dashboard payloads
- get_sse_manager singleton
"""

import asyncio
from unittest.mock import MagicMock

import pytest

import src.core.event_bus as event_bus
from src.core.event_bus import Event, EventBus
from src.raas.sse import (
    HUMAN_MESSAGES,
    EventBusAdapter,
    SSEManager,
    get_sse_manager,
    reset_sse_manager,
)

# Resolve EventType through the module attribute (not a captured alias).
#
# The conftest session-scoped patches swap ``src.core.event_bus.EventType``
# for a MagicMock at collection time, so a bare ``from ... import EventType``
# taken here would bind to that mock for the whole file.  Tests therefore
# reference ``event_bus.EventType`` directly so the session fixture's
# restore (``restore_real_event_types``) is visible at call time.


# --------------------------------------------------------------------------- #
# SSEManager
# --------------------------------------------------------------------------- #


pytestmark = pytest.mark.usefixtures("restore_real_event_types")


def test_sse_manager_starts_empty():
    mgr = SSEManager()
    assert mgr.connections == {}


def test_register_creates_queue_and_appends():
    mgr = SSEManager()
    q1 = mgr.register("tenant-a")
    q2 = mgr.register("tenant-a")
    q3 = mgr.register("tenant-b")

    assert isinstance(q1, asyncio.Queue)
    assert q1 is not q2
    assert q3 is not q1
    assert len(mgr.connections["tenant-a"]) == 2
    assert len(mgr.connections["tenant-b"]) == 1


def test_unregister_removes_queue_and_cleans_tenant():
    mgr = SSEManager()
    q = mgr.register("tenant-a")
    mgr.unregister("tenant-a", q)

    assert "tenant-a" not in mgr.connections
    # unregister on unknown tenant is a no-op
    mgr.unregister("ghost", q)


def test_unregister_keeps_other_queues_for_tenant():
    mgr = SSEManager()
    q1 = mgr.register("tenant-a")
    q2 = mgr.register("tenant-a")
    mgr.unregister("tenant-a", q1)

    assert len(mgr.connections["tenant-a"]) == 1
    assert q2 in mgr.connections["tenant-a"]


def test_push_delivers_to_all_tenant_queues():
    mgr = SSEManager()
    q1 = mgr.register("tenant-a")
    q2 = mgr.register("tenant-a")
    payload = {"type": "goal_completed", "message": "Mission completed"}

    mgr.push("tenant-a", payload)

    assert q1.get_nowait() == payload
    assert q2.get_nowait() == payload


def test_push_to_unknown_tenant_is_noop():
    mgr = SSEManager()
    mgr.push("nobody", {"type": "x"})
    assert mgr.connections == {}


def test_push_drops_on_full_queue():
    mgr = SSEManager()
    # Inject a queue-like object whose put_nowait raises QueueFull.
    full_queue = MagicMock()
    full_queue.put_nowait.side_effect = asyncio.QueueFull
    mgr.connections["tenant-a"] = [full_queue]

    # A QueueFull must never propagate out of push().
    mgr.push("tenant-a", {"type": "x"})
    full_queue.put_nowait.assert_called_once_with({"type": "x"})


def test_push_handles_maxsize_queue_overflow():
    mgr = SSEManager()
    q = asyncio.Queue(maxsize=1)
    q.put_nowait("filler")  # queue is now full
    mgr.connections["tenant-a"] = [q]

    mgr.push("tenant-a", {"type": "x"})  # must not raise


# --------------------------------------------------------------------------- #
# EventBusAdapter
# --------------------------------------------------------------------------- #


def _make_event(event_type, **data):
    return Event(type=event_type, data=data)


def test_adapter_subscribes_to_every_event_type():
    bus = EventBus()
    EventBusAdapter(SSEManager(), bus)  # subscription side-effect only
    # One subscriber callback per declared EventType.
    assert bus.subscriber_count == len(list(event_bus.EventType))


def test_translate_known_event_type():
    bus = EventBus()
    adapter = EventBusAdapter(SSEManager(), bus)
    event = _make_event(event_bus.EventType.GOAL_STARTED)

    assert adapter._translate(event) == HUMAN_MESSAGES["GOAL_STARTED"]


def test_translate_resource_exhausted_via_error_field():
    bus = EventBus()
    adapter = EventBusAdapter(SSEManager(), bus)
    event = _make_event(
        event_bus.EventType.STEP_FAILED,
        error="RESOURCE_EXHAUSTED: rate limit hit, retry in 2 minutes",
    )

    assert adapter._translate(event) == HUMAN_MESSAGES["RESOURCE_EXHAUSTED"]


def test_translate_unknown_event_type_falls_back_to_title():
    bus = EventBus()
    adapter = EventBusAdapter(SSEManager(), bus)
    # A type with no HUMAN_MESSAGES entry falls back to the enum value,
    # underscored words title-cased.
    event = _make_event(event_bus.EventType.HALT_TRIGGERED)

    assert adapter._translate(event) == "Halt Triggered"


def test_handle_routes_event_to_correct_tenant():
    sse = SSEManager()
    bus = EventBus()
    adapter = EventBusAdapter(sse, bus)
    queue = sse.register("tenant-a")

    adapter._handle(_make_event(event_bus.EventType.GOAL_COMPLETED, tenant_id="tenant-a"))

    payload = queue.get_nowait()
    assert payload["type"] == event_bus.EventType.GOAL_COMPLETED.value
    assert payload["message"] == "Mission completed"
    assert payload["data"]["tenant_id"] == "tenant-a"
    assert "timestamp" in payload


def test_handle_ignores_events_without_tenant_id():
    sse = SSEManager()
    bus = EventBus()
    adapter = EventBusAdapter(sse, bus)
    sse.register("tenant-a")
    before = dict(sse.connections)

    adapter._handle(_make_event(event_bus.EventType.GOAL_STARTED))

    assert sse.connections == before


def test_adapter_subscribed_via_bus_receives_events():
    sse = SSEManager()
    bus = EventBus()
    EventBusAdapter(sse, bus)
    queue = sse.register("tenant-a")

    bus.emit(event_bus.EventType.GOAL_COMPLETED, {"tenant_id": "tenant-a"})

    # The adapter is subscribed to the bus, so the emitted event is
    # translated and pushed to the tenant queue.
    payload = queue.get_nowait()
    assert payload["type"] == event_bus.EventType.GOAL_COMPLETED.value
    assert payload["message"] == HUMAN_MESSAGES["GOAL_COMPLETED"]


# --------------------------------------------------------------------------- #
# Singleton
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _reset_singleton():
    reset_sse_manager()
    yield
    reset_sse_manager()


def test_get_sse_manager_returns_singleton():
    first = get_sse_manager()
    second = get_sse_manager()
    assert first is second
    assert isinstance(first, SSEManager)


def test_reset_sse_manager_breaks_singleton():
    first = get_sse_manager()
    reset_sse_manager()
    second = get_sse_manager()
    assert first is not second