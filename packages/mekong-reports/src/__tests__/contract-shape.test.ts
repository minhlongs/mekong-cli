/**
 * Contract shape tests — verify data returned matches TypeScript interfaces.
 * These tests are the stability signal: if they pass, consumers won't break.
 */

import { describe, it, expect } from "vitest";
import { getDepartmentCommands } from "../departments.js";
import { getPricingTiers } from "../pricing.js";
import { getMission, listMissions } from "../missions.js";

// ─── getDepartmentCommands ────────────────────────────────────────────────────

describe("getDepartmentCommands", () => {
  it("returns engineering commands with required fields", async () => {
    const result = await getDepartmentCommands("engineering");
    expect(result.source).toBe("mock");
    expect(result.data.length).toBeGreaterThan(0);

    const cmd = result.data[0];
    expect(typeof cmd.slug).toBe("string");
    expect(typeof cmd.title).toBe("string");
    expect(typeof cmd.description).toBe("string");
    expect(typeof cmd.mcu).toBe("number");
    expect(cmd.mcu).toBeGreaterThan(0);
  });

  it("returns 10 engineering commands matching B1 hardcoded count", async () => {
    const result = await getDepartmentCommands("engineering");
    expect(result.data).toHaveLength(10);
  });

  it("returns empty array for unknown department slug", async () => {
    const result = await getDepartmentCommands("nonexistent");
    expect(result.data).toHaveLength(0);
    expect(result.source).toBe("mock");
  });
});

// ─── getPricingTiers ──────────────────────────────────────────────────────────

describe("getPricingTiers", () => {
  it("returns exactly 3 tiers", () => {
    const tiers = getPricingTiers();
    expect(tiers).toHaveLength(3);
  });

  it("each tier has required fields with valid values", () => {
    const tiers = getPricingTiers();
    for (const tier of tiers) {
      expect(typeof tier.id).toBe("string");
      expect(typeof tier.name).toBe("string");
      expect(tier.priceUsdCents).toBeGreaterThan(0);
      expect(tier.creditsPerMonth).toBeGreaterThan(0);
      expect(tier.checkoutUrl).toMatch(/^https:\/\//);
      expect(Array.isArray(tier.features)).toBe(true);
      expect(tier.features.length).toBeGreaterThan(0);
    }
  });

  it("exactly one tier is highlighted", () => {
    const tiers = getPricingTiers();
    const highlighted = tiers.filter((t) => t.highlighted);
    expect(highlighted).toHaveLength(1);
  });
});

// ─── getMission / listMissions ────────────────────────────────────────────────

describe("getMission", () => {
  it("returns mission when id exists", async () => {
    const result = await getMission("msn_001");
    expect(result.data).not.toBeNull();
    expect(result.data?.id).toBe("msn_001");
    expect(result.data?.status).toBe("completed");
    expect(typeof result.data?.createdAt).toBe("string");
  });

  it("returns null for unknown id", async () => {
    const result = await getMission("msn_9999");
    expect(result.data).toBeNull();
    expect(result.source).toBe("mock");
  });
});

describe("listMissions", () => {
  it("returns all missions when no filter applied", async () => {
    const result = await listMissions();
    expect(result.data.length).toBeGreaterThan(0);
    expect(result.fetchedAt).toBeGreaterThan(0);
  });

  it("filters by status correctly", async () => {
    const result = await listMissions({ status: "completed" });
    expect(result.data.every((m) => m.status === "completed")).toBe(true);
  });
});
