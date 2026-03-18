import { describe, it, expect, beforeEach } from "vitest";
import { DashboardApi } from "../src/api.js";

describe("DashboardApi", () => {
  let api: DashboardApi;

  beforeEach(() => {
    api = new DashboardApi("0.1.0");
  });

  it("rejects non-GET methods with 405", () => {
    const r = api.handleRequest("POST", "/status");
    expect(r.status).toBe(405);
  });

  it("returns 404 for unknown routes", () => {
    const r = api.handleRequest("GET", "/unknown");
    expect(r.status).toBe(404);
  });

  it("GET /status returns uptime, version, paneCount, taskCount", () => {
    const r = api.handleRequest("GET", "/status");
    expect(r.status).toBe(200);
    const b = r.body as Record<string, unknown>;
    expect(b.version).toBe("0.1.0");
    expect(typeof b.uptime).toBe("number");
    expect(typeof b.paneCount).toBe("number");
    expect(typeof b.taskCount).toBe("number");
  });

  it("GET /panes returns panes array", () => {
    const r = api.handleRequest("GET", "/panes");
    expect(r.status).toBe(200);
    const b = r.body as { panes: unknown[] };
    expect(Array.isArray(b.panes)).toBe(true);
    expect(b.panes.length).toBeGreaterThan(0);
  });

  it("GET /tasks returns queued/active/completed", () => {
    const r = api.handleRequest("GET", "/tasks");
    expect(r.status).toBe(200);
    const b = r.body as Record<string, unknown[]>;
    expect(Array.isArray(b.queued)).toBe(true);
    expect(Array.isArray(b.active)).toBe(true);
    expect(Array.isArray(b.completed)).toBe(true);
  });

  it("GET /raas returns tenants, revenue, health", () => {
    const r = api.handleRequest("GET", "/raas");
    expect(r.status).toBe(200);
    const b = r.body as Record<string, unknown>;
    expect(typeof b.tenants).toBe("number");
    expect(typeof b.revenue).toBe("number");
    expect(typeof b.health).toBe("string");
  });

  it("GET /agi-score returns score and capabilitiesCount", () => {
    const r = api.handleRequest("GET", "/agi-score");
    expect(r.status).toBe(200);
    const b = r.body as Record<string, unknown>;
    expect(typeof b.score).toBe("number");
    expect(typeof b.capabilitiesCount).toBe("number");
    expect(Array.isArray(b.capabilities)).toBe(true);
  });

  it("registerWebSocketHandler accepts a callback without throwing", () => {
    expect(() => api.registerWebSocketHandler(() => {})).not.toThrow();
  });

  it("contentType is application/json for all routes", () => {
    const routes = ["/status", "/panes", "/tasks", "/raas", "/agi-score"];
    for (const path of routes) {
      expect(api.handleRequest("GET", path).contentType).toBe("application/json");
    }
  });
});
