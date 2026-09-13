"""
Tests: src.core.event_bus — EventType, Event, EventBus, EventStream, StreamingEventBus.

Covers:
- EventType enum values and string identity
- Event dataclass field defaults and assignment
- EventBus: subscribe / unsubscribe / emit / clear / subscriber_count
- EventBus: error isolation (subscriber exceptions don't break dispatch)
- EventStream: push / read / cursor / buffered_count / clear / max_buffer eviction
- StreamingEventBus: dual subscriber + stream behaviour
- Singleton helpers: get_event_bus / get_streaming_bus + module-level cache reset
"""

from __future__ import annotations

import time

import pytest

from src.core import event_bus as eb_mod
from src.core.event_bus import (
    Event,
    EventBus,
    EventStream,
    EventType,
    StreamingEventBus,
    get_event_bus,
    get_streaming_bus,
)


# ---------------------------------------------------------------------------
# Singleton reset — tests must not leak the global bus
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_default_bus():
    """Reset module-level singleton before/after each test."""
    eb_mod._default_bus = None
    yield
    eb_mod._default_bus = None


# ---------------------------------------------------------------------------
# EventType enum
# ---------------------------------------------------------------------------

class TestEventType:

    def test_string_enum(self):
        assert isinstance(EventType.GOAL_STARTED, str)
        assert EventType.GOAL_STARTED == "goal_started"

    def test_namespaced_event_value(self):
        assert EventType.LICENSE_CRITICAL.value == "license:critical"

    def test_billing_namespace(self):
        assert EventType.BILLING_RECORDED.value == "billing:recorded"

    def test_recovery_namespace(self):
        assert EventType.RECOVERY_SUCCESS.value == "recovery:success"

    def test_all_values_unique(self):
        values = [e.value for e in EventType]
        assert len(values) == len(set(values))


# ---------------------------------------------------------------------------
# Event dataclass
# ---------------------------------------------------------------------------

class TestEvent:

    def test_required_type(self):
        ev = Event(type=EventType.GOAL_STARTED)
        assert ev.type == EventType.GOAL_STARTED

    def test_default_data_empty_dict(self):
        ev = Event(type=EventType.GOAL_STARTED)
        assert ev.data == {}

    def test_default_data_independent_per_instance(self):
        a = Event(type=EventType.GOAL_STARTED)
        b = Event(type=EventType.GOAL_STARTED)
        a.data["k"] = 1
        assert b.data == {}

    def test_timestamp_auto_populated(self):
        before = time.time()
        ev = Event(type=EventType.GOAL_STARTED)
        after = time.time()
        assert before <= ev.timestamp <= after

    def test_data_passed_through(self):
        ev = Event(type=EventType.STEP_COMPLETED, data={"step": 3})
        assert ev.data == {"step": 3}


# ---------------------------------------------------------------------------
# EventBus.subscribe / unsubscribe / subscriber_count
# ---------------------------------------------------------------------------

class TestEventBusSubscription:

    def test_subscribe_adds_callback(self):
        bus = EventBus()
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        assert bus.subscriber_count == 1

    def test_subscribe_multiple_same_type(self):
        bus = EventBus()
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        assert bus.subscriber_count == 2

    def test_subscribe_different_types(self):
        bus = EventBus()
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        bus.subscribe(EventType.GOAL_COMPLETED, lambda e: None)
        assert bus.subscriber_count == 2

    def test_unsubscribe_removes_callback(self):
        bus = EventBus()
        cb = lambda e: None  # noqa: E731
        bus.subscribe(EventType.GOAL_STARTED, cb)
        bus.unsubscribe(EventType.GOAL_STARTED, cb)
        assert bus.subscriber_count == 0

    def test_unsubscribe_unknown_callback_is_noop(self):
        bus = EventBus()
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        bus.unsubscribe(EventType.GOAL_STARTED, lambda e: None)  # different cb
        assert bus.subscriber_count == 1

    def test_unsubscribe_unknown_event_type_is_noop(self):
        bus = EventBus()
        bus.unsubscribe(EventType.GOAL_STARTED, lambda e: None)
        assert bus.subscriber_count == 0

    def test_subscriber_count_zero_initially(self):
        assert EventBus().subscriber_count == 0

    def test_unsubscribe_twice_is_idempotent(self):
        bus = EventBus()
        cb = lambda e: None  # noqa: E731
        bus.subscribe(EventType.GOAL_STARTED, cb)
        bus.unsubscribe(EventType.GOAL_STARTED, cb)
        bus.unsubscribe(EventType.GOAL_STARTED, cb)  # second call is no-op
        assert bus.subscriber_count == 0


# ---------------------------------------------------------------------------
# EventBus.emit
# ---------------------------------------------------------------------------

class TestEventBusEmit:

    def test_emit_returns_event(self):
        bus = EventBus()
        ev = bus.emit(EventType.GOAL_STARTED, {"id": 1})
        assert isinstance(ev, Event)
        assert ev.type == EventType.GOAL_STARTED
        assert ev.data == {"id": 1}

    def test_emit_calls_subscriber(self):
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe(EventType.GOAL_STARTED, received.append)
        bus.emit(EventType.GOAL_STARTED, {"x": 1})
        assert len(received) == 1
        assert received[0].data == {"x": 1}

    def test_emit_calls_all_subscribers(self):
        bus = EventBus()
        a: list[Event] = []
        b: list[Event] = []
        bus.subscribe(EventType.GOAL_STARTED, a.append)
        bus.subscribe(EventType.GOAL_STARTED, b.append)
        bus.emit(EventType.GOAL_STARTED)
        assert len(a) == 1
        assert len(b) == 1

    def test_emit_does_not_call_other_type_subscribers(self):
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe(EventType.GOAL_COMPLETED, received.append)
        bus.emit(EventType.GOAL_STARTED)
        assert received == []

    def test_emit_with_none_data_yields_empty_dict(self):
        bus = EventBus()
        ev = bus.emit(EventType.GOAL_STARTED, None)
        assert ev.data == {}

    def test_emit_with_no_subscribers_does_not_raise(self):
        bus = EventBus()
        ev = bus.emit(EventType.GOAL_STARTED)
        assert ev.type == EventType.GOAL_STARTED

    def test_emit_isolates_subscriber_exceptions(self):
        bus = EventBus()
        received: list[Event] = []

        def boom(_: Event) -> None:
            raise RuntimeError("subscriber failed")

        bus.subscribe(EventType.GOAL_STARTED, boom)
        bus.subscribe(EventType.GOAL_STARTED, received.append)
        bus.emit(EventType.GOAL_STARTED)
        # Second subscriber must still be invoked despite first one raising
        assert len(received) == 1

    def test_emit_subscriber_call_order(self):
        bus = EventBus()
        order: list[str] = []
        bus.subscribe(EventType.GOAL_STARTED, lambda e: order.append("first"))
        bus.subscribe(EventType.GOAL_STARTED, lambda e: order.append("second"))
        bus.emit(EventType.GOAL_STARTED)
        assert order == ["first", "second"]


# ---------------------------------------------------------------------------
# EventBus.clear
# ---------------------------------------------------------------------------

class TestEventBusClear:

    def test_clear_resets_subscribers(self):
        bus = EventBus()
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        bus.subscribe(EventType.GOAL_COMPLETED, lambda e: None)
        bus.clear()
        assert bus.subscriber_count == 0

    def test_clear_then_emit_works(self):
        bus = EventBus()
        bus.subscribe(EventType.GOAL_STARTED, lambda e: None)
        bus.clear()
        # Should not raise
        bus.emit(EventType.GOAL_STARTED)


# ---------------------------------------------------------------------------
# EventStream
# ---------------------------------------------------------------------------

class TestEventStream:

    def test_initial_empty(self):
        s = EventStream()
        assert s.buffered_count == 0
        assert s.cursor == 0

    def test_push_increments_buffered(self):
        s = EventStream()
        s.push(Event(type=EventType.GOAL_STARTED))
        assert s.buffered_count == 1

    def test_push_increments_cursor(self):
        s = EventStream()
        s.push(Event(type=EventType.GOAL_STARTED))
        s.push(Event(type=EventType.GOAL_COMPLETED))
        assert s.cursor == 2

    def test_max_buffer_evicts_oldest(self):
        s = EventStream(max_buffer=2)
        s.push(Event(type=EventType.GOAL_STARTED, data={"i": 1}))
        s.push(Event(type=EventType.GOAL_STARTED, data={"i": 2}))
        s.push(Event(type=EventType.GOAL_STARTED, data={"i": 3}))
        assert s.buffered_count == 2
        assert s.cursor == 3
        events = s.read(since_cursor=0)
        assert [e.data["i"] for e in events] == [2, 3]

    def test_read_from_zero_returns_all_buffered(self):
        s = EventStream()
        for i in range(3):
            s.push(Event(type=EventType.GOAL_STARTED, data={"i": i}))
        events = s.read(since_cursor=0)
        assert len(events) == 3

    def test_read_with_limit(self):
        s = EventStream()
        for i in range(5):
            s.push(Event(type=EventType.GOAL_STARTED, data={"i": i}))
        events = s.read(since_cursor=0, limit=2)
        assert len(events) == 2

    def test_read_since_cursor_skips_earlier_events(self):
        s = EventStream()
        for i in range(4):
            s.push(Event(type=EventType.GOAL_STARTED, data={"i": i}))
        events = s.read(since_cursor=2)
        assert [e.data["i"] for e in events] == [2, 3]

    def test_read_cursor_beyond_total_returns_empty(self):
        s = EventStream()
        s.push(Event(type=EventType.GOAL_STARTED))
        events = s.read(since_cursor=10)
        assert events == []

    def test_read_handles_evicted_cursor(self):
        """If cursor points to an evicted event, return what remains in buffer."""
        s = EventStream(max_buffer=3)
        for i in range(6):  # cursor 0..5; buffer keeps last 3 (3,4,5)
            s.push(Event(type=EventType.GOAL_STARTED, data={"i": i}))
        events = s.read(since_cursor=0)
        # buffer_start = 6 - 3 = 3, skip = max(0, 0 - 3) = 0 → returns full buffer
        assert [e.data["i"] for e in events] == [3, 4, 5]

    def test_read_cursor_inside_evicted_window(self):
        """cursor pointing at an evicted-but-still-counted position clamps to buffer_start."""
        s = EventStream(max_buffer=3)
        for i in range(6):
            s.push(Event(type=EventType.GOAL_STARTED, data={"i": i}))
        # buffer_start=3, cursor=2 (evicted) → skip=max(0, 2-3)=0 → returns full buffer
        events = s.read(since_cursor=2)
        assert [e.data["i"] for e in events] == [3, 4, 5]

    def test_read_with_zero_limit_returns_empty(self):
        s = EventStream()
        s.push(Event(type=EventType.GOAL_STARTED))
        assert s.read(since_cursor=0, limit=0) == []

    def test_clear_then_push_continues_cursor(self):
        s = EventStream()
        s.push(Event(type=EventType.GOAL_STARTED))
        s.clear()
        s.push(Event(type=EventType.GOAL_COMPLETED))
        # cursor reflects all-time emits; buffer reflects current state
        assert s.cursor == 2
        assert s.buffered_count == 1

    def test_clear_empties_buffer_but_preserves_cursor(self):
        s = EventStream()
        s.push(Event(type=EventType.GOAL_STARTED))
        s.push(Event(type=EventType.GOAL_COMPLETED))
        s.clear()
        assert s.buffered_count == 0
        # Cursor is total_emitted — clear() does not reset it
        assert s.cursor == 2


# ---------------------------------------------------------------------------
# StreamingEventBus
# ---------------------------------------------------------------------------

class TestStreamingEventBus:

    def test_emit_pushes_to_stream(self):
        bus = StreamingEventBus()
        bus.emit(EventType.GOAL_STARTED, {"id": 1})
        assert bus.stream.buffered_count == 1

    def test_emit_calls_subscribers_and_streams(self):
        bus = StreamingEventBus()
        received: list[Event] = []
        bus.subscribe(EventType.GOAL_STARTED, received.append)
        bus.emit(EventType.GOAL_STARTED)
        assert len(received) == 1
        assert bus.stream.buffered_count == 1

    def test_emit_returns_event(self):
        bus = StreamingEventBus()
        ev = bus.emit(EventType.GOAL_STARTED, {"id": 7})
        assert ev.data == {"id": 7}

    def test_max_buffer_passed_through(self):
        bus = StreamingEventBus(max_buffer=2)
        for i in range(4):
            bus.emit(EventType.GOAL_STARTED, {"i": i})
        assert bus.stream.buffered_count == 2
        assert bus.stream.cursor == 4

    def test_subscriber_exception_does_not_break_streaming(self):
        bus = StreamingEventBus()

        def boom(_: Event) -> None:
            raise ValueError("oops")

        bus.subscribe(EventType.GOAL_STARTED, boom)
        bus.emit(EventType.GOAL_STARTED)
        # Stream should still have received the event despite subscriber error
        assert bus.stream.buffered_count == 1


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

class TestGetEventBus:

    def test_returns_event_bus_instance(self):
        assert isinstance(get_event_bus(), EventBus)

    def test_returns_same_instance_on_repeat_calls(self):
        a = get_event_bus()
        b = get_event_bus()
        assert a is b

    def test_state_persists_across_calls(self):
        get_event_bus().subscribe(EventType.GOAL_STARTED, lambda e: None)
        assert get_event_bus().subscriber_count == 1


class TestGetStreamingBus:

    def test_returns_streaming_bus(self):
        assert isinstance(get_streaming_bus(), StreamingEventBus)

    def test_upgrades_plain_bus_to_streaming(self):
        plain = get_event_bus()
        assert not isinstance(plain, StreamingEventBus)
        upgraded = get_streaming_bus()
        assert isinstance(upgraded, StreamingEventBus)
        # The old plain reference is replaced by the new singleton
        assert get_event_bus() is upgraded

    def test_repeat_calls_return_same_streaming_instance(self):
        a = get_streaming_bus()
        b = get_streaming_bus()
        assert a is b

    def test_max_buffer_used_only_on_creation(self):
        first = get_streaming_bus(max_buffer=10)
        # Subsequent call returns same instance even with different max_buffer
        second = get_streaming_bus(max_buffer=999)
        assert first is second


# ---------------------------------------------------------------------------
# __all__ public surface
# ---------------------------------------------------------------------------

class TestPublicSurface:

    def test_all_names_importable(self):
        for name in eb_mod.__all__:
            assert hasattr(eb_mod, name)

    def test_all_includes_core_classes(self):
        names = set(eb_mod.__all__)
        assert {"Event", "EventBus", "EventType", "EventStream", "StreamingEventBus"} <= names
