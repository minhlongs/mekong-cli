import { describe, it, expect, beforeEach, vi } from "vitest";
import { DashboardEventBus } from "../src/event-bus.js";

describe("DashboardEventBus", () => {
  let bus: DashboardEventBus;

  beforeEach(() => {
    bus = new DashboardEventBus();
  });

  it("calls registered handler when event emitted", () => {
    const handler = vi.fn();
    bus.on("pane:status", handler);
    bus.emit("pane:status", { id: "pane-0", state: "running" });
    expect(handler).toHaveBeenCalledOnce();
    expect(handler).toHaveBeenCalledWith({ id: "pane-0", state: "running" });
  });

  it("does not call handler after off()", () => {
    const handler = vi.fn();
    bus.on("task:created", handler);
    bus.off("task:created", handler);
    bus.emit("task:created", {});
    expect(handler).not.toHaveBeenCalled();
  });

  it("multiple handlers on same event all called", () => {
    const h1 = vi.fn();
    const h2 = vi.fn();
    bus.on("agi:evolved", h1);
    bus.on("agi:evolved", h2);
    bus.emit("agi:evolved", { score: 50 });
    expect(h1).toHaveBeenCalledOnce();
    expect(h2).toHaveBeenCalledOnce();
  });

  it("does not call handlers on other events", () => {
    const handler = vi.fn();
    bus.on("raas:credit", handler);
    bus.emit("task:completed", {});
    expect(handler).not.toHaveBeenCalled();
  });

  it("stores event in history", () => {
    bus.emit("pane:status", "data");
    const history = bus.getHistory();
    expect(history).toHaveLength(1);
    expect(history[0]!.event).toBe("pane:status");
    expect(history[0]!.data).toBe("data");
    expect(typeof history[0]!.timestamp).toBe("number");
  });

  it("getHistory filtered by event name", () => {
    bus.emit("pane:status", 1);
    bus.emit("task:created", 2);
    bus.emit("pane:status", 3);
    const history = bus.getHistory("pane:status");
    expect(history).toHaveLength(2);
    expect(history.every((r) => r.event === "pane:status")).toBe(true);
  });

  it("getHistory with limit returns most recent N", () => {
    for (let i = 0; i < 5; i++) bus.emit("pane:status", i);
    const limited = bus.getHistory(undefined, 3);
    expect(limited).toHaveLength(3);
    // Most recent first — last emitted data is 4
    expect(limited[0]!.data).toBe(4);
  });

  it("getHistory returns most recent first (no filter)", () => {
    bus.emit("pane:status", "first");
    bus.emit("pane:status", "second");
    const history = bus.getHistory();
    expect(history[0]!.data).toBe("second");
  });

  it("evicts oldest event when history exceeds 1000", () => {
    for (let i = 0; i < 1001; i++) bus.emit("pane:status", i);
    expect(bus.historySize).toBe(1000);
    // Oldest (data=0) should be gone; most recent in history (order reversed) = 1000
    const all = bus.getHistory();
    expect(all[0]!.data).toBe(1000);
  });

  it("isolates handler errors — other handlers still called", () => {
    const bad = vi.fn(() => { throw new Error("boom"); });
    const good = vi.fn();
    bus.on("pane:status", bad);
    bus.on("pane:status", good);
    expect(() => bus.emit("pane:status", {})).not.toThrow();
    expect(good).toHaveBeenCalledOnce();
  });

  it("clear() removes all handlers and history", () => {
    const handler = vi.fn();
    bus.on("pane:status", handler);
    bus.emit("pane:status", {});
    bus.clear();
    bus.emit("pane:status", {});
    expect(handler).toHaveBeenCalledOnce(); // only the pre-clear call
    expect(bus.historySize).toBe(1); // post-clear emit stored fresh
  });

  it("off() on unregistered event is a no-op", () => {
    expect(() => bus.off("nonexistent", vi.fn())).not.toThrow();
  });
});
