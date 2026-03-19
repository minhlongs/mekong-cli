import { describe, it, expect, beforeAll, afterAll } from "vitest";
import http from "node:http";
import { startServer, stopServer } from "./server.js";

const PORT = 13333;

let server: http.Server;

beforeAll(() => {
  server = startServer(PORT);
});

afterAll(() => {
  stopServer(server);
});

async function get(path: string): Promise<{ status: number; body: string; contentType: string }> {
  return new Promise((resolve, reject) => {
    http.get(`http://localhost:${PORT}${path}`, (res) => {
      let body = "";
      res.on("data", (chunk: Buffer) => { body += chunk.toString(); });
      res.on("end", () => {
        resolve({
          status: res.statusCode ?? 0,
          body,
          contentType: String(res.headers["content-type"] ?? ""),
        });
      });
    }).on("error", reject);
  });
}

describe("server routes", () => {
  it("GET / returns dashboard HTML with 200", async () => {
    const r = await get("/");
    expect(r.status).toBe(200);
    expect(r.contentType).toContain("text/html");
    expect(r.body).toContain("AgencyOS");
  });

  it("GET /license returns license HTML with 200", async () => {
    const r = await get("/license");
    expect(r.status).toBe(200);
    expect(r.contentType).toContain("text/html");
    expect(r.body).toContain("License");
  });

  it("GET /raas returns raas HTML with 200", async () => {
    const r = await get("/raas");
    expect(r.status).toBe(200);
    expect(r.contentType).toContain("text/html");
    expect(r.body).toContain("RaaS");
  });

  it("GET /api/status returns JSON with required fields", async () => {
    const r = await get("/api/status");
    expect(r.status).toBe(200);
    expect(r.contentType).toContain("application/json");
    const data = JSON.parse(r.body) as Record<string, unknown>;
    expect(data.status).toBe("online");
    expect(data.version).toBe("0.1.0");
    expect(typeof data.timestamp).toBe("string");
    const company = data.company as Record<string, unknown>;
    expect(typeof company.health).toBe("number");
    expect(Array.isArray(company.departments)).toBe(true);
  });

  it("GET /unknown returns 404", async () => {
    const r = await get("/not-a-page");
    expect(r.status).toBe(404);
  });

  it("security headers present on dashboard", async () => {
    const r = await new Promise<http.IncomingMessage>((resolve, reject) => {
      http.get(`http://localhost:${PORT}/`, resolve).on("error", reject);
    });
    expect(r.headers["x-frame-options"]).toBe("DENY");
    expect(r.headers["x-content-type-options"]).toBe("nosniff");
  });
});
