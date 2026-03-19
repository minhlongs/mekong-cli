import { describe, it, expect, beforeEach } from "vitest";
import { WebSocketRelay } from "./ws.js";

describe("WebSocketRelay", () => {
  let relay: WebSocketRelay;

  beforeEach(() => {
    relay = new WebSocketRelay();
  });

  it("starts with 0 connections", () => {
    expect(relay.getConnectionCount()).toBe(0);
  });

  it("tracks connect/disconnect", () => {
    relay.connect();
    relay.connect();
    expect(relay.getConnectionCount()).toBe(2);
    relay.disconnect();
    expect(relay.getConnectionCount()).toBe(1);
  });

  it("disconnect does not go below 0", () => {
    relay.disconnect();
    expect(relay.getConnectionCount()).toBe(0);
  });

  it("broadcast delivers event to listener", () => {
    const received: unknown[] = [];
    relay.on("status", (data) => { received.push(data); });
    relay.broadcast("status", { health: 90 });
    expect(received).toHaveLength(1);
    expect(received[0]).toEqual({ health: 90 });
  });

  it("off removes listener", () => {
    const received: unknown[] = [];
    const handler = (data: unknown) => { received.push(data); };
    relay.on("update", handler);
    relay.off("update", handler);
    relay.broadcast("update", "ping");
    expect(received).toHaveLength(0);
  });

  it("broadcast to unregistered event does nothing", () => {
    expect(() => relay.broadcast("noop", null)).not.toThrow();
  });

  it("destroy resets connections and listeners", () => {
    const received: unknown[] = [];
    relay.on("ev", (d) => { received.push(d); });
    relay.connect();
    relay.destroy();
    relay.broadcast("ev", "x");
    expect(received).toHaveLength(0);
    expect(relay.getConnectionCount()).toBe(0);
  });
});
