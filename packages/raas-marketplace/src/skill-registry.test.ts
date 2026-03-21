// Tests for skill-package.ts and skill-registry.ts

import { describe, it, expect, beforeEach } from "vitest";
import {
  validateManifest,
  createPackageId,
  parsePackageId,
  type SkillManifest,
  type SkillPackage,
} from "./skill-package.js";
import { SkillRegistry } from "./skill-registry.js";

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function createTestPackage(overrides: Partial<SkillPackage> = {}): SkillPackage {
  return {
    manifest: {
      name: "test-skill",
      version: "1.0.0",
      description: "A test skill for unit testing",
      author: "tester",
      license: "MIT",
      tags: ["test", "utility"],
      triggers: ["test"],
    },
    readme: "# Test Skill",
    files: [],
    publishedAt: new Date("2024-01-01"),
    downloads: 0,
    rating: 0,
    ratingCount: 0,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// skill-package tests
// ---------------------------------------------------------------------------

describe("validateManifest", () => {
  it("returns valid for a correct manifest", () => {
    const manifest: SkillManifest = {
      name: "my-skill",
      version: "1.0.0",
      description: "Does something useful",
      author: "dev",
      license: "MIT",
      tags: [],
      triggers: ["activate"],
    };
    const result = validateManifest(manifest);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("returns error when name is missing", () => {
    const manifest = {
      name: "",
      version: "1.0.0",
      description: "desc",
      author: "dev",
      license: "MIT",
      tags: [],
      triggers: [],
    } as SkillManifest;
    const result = validateManifest(manifest);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("name"))).toBe(true);
  });

  it("returns error for invalid semver version", () => {
    const manifest: SkillManifest = {
      name: "my-skill",
      version: "not-semver",
      description: "desc",
      author: "dev",
      license: "MIT",
      tags: [],
      triggers: [],
    };
    const result = validateManifest(manifest);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("semver"))).toBe(true);
  });

  it("returns error when name is too short (< 3 chars)", () => {
    const manifest: SkillManifest = {
      name: "ab",
      version: "1.0.0",
      description: "desc",
      author: "dev",
      license: "MIT",
      tags: [],
      triggers: [],
    };
    const result = validateManifest(manifest);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("name"))).toBe(true);
  });
});

describe("createPackageId", () => {
  it("returns name@version format", () => {
    expect(createPackageId("my-skill", "2.1.0")).toBe("my-skill@2.1.0");
  });
});

describe("parsePackageId", () => {
  it("parses a valid package id", () => {
    expect(parsePackageId("my-skill@1.0.0")).toEqual({
      name: "my-skill",
      version: "1.0.0",
    });
  });

  it("returns null for an invalid id", () => {
    expect(parsePackageId("no-at-sign")).toBeNull();
    expect(parsePackageId("@missing-name")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// skill-registry tests
// ---------------------------------------------------------------------------

describe("SkillRegistry", () => {
  let registry: SkillRegistry;

  beforeEach(() => {
    registry = new SkillRegistry();
  });

  it("publish — publishes a valid package", () => {
    const pkg = createTestPackage();
    const result = registry.publish(pkg);
    expect(result.success).toBe(true);
    expect(registry.getLatest("test-skill")).toBeDefined();
  });

  it("publish — rejects duplicate version", () => {
    const pkg = createTestPackage();
    registry.publish(pkg);
    const result = registry.publish(pkg);
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/already exists/);
  });

  it("search — finds by name match", () => {
    registry.publish(createTestPackage());
    const results = registry.search("test-skill");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].manifest.name).toBe("test-skill");
  });

  it("search — finds by tag match", () => {
    registry.publish(createTestPackage());
    const results = registry.search("utility");
    expect(results.length).toBeGreaterThan(0);
  });

  it("search — returns empty array for no match", () => {
    registry.publish(createTestPackage());
    const results = registry.search("zzznomatch");
    expect(results).toHaveLength(0);
  });

  it("getLatest — returns latest version", () => {
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, version: "1.0.0" } }));
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, version: "1.1.0" } }));
    const latest = registry.getLatest("test-skill");
    expect(latest?.manifest.version).toBe("1.1.0");
  });

  it("getVersion — returns specific version", () => {
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, version: "1.0.0" } }));
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, version: "2.0.0" } }));
    const pkg = registry.getVersion("test-skill", "1.0.0");
    expect(pkg?.manifest.version).toBe("1.0.0");
  });

  it("rate — updates rating", () => {
    registry.publish(createTestPackage());
    const ok = registry.rate("test-skill", 4);
    expect(ok).toBe(true);
    const pkg = registry.getLatest("test-skill");
    expect(pkg?.rating).toBe(4);
    expect(pkg?.ratingCount).toBe(1);
  });

  it("getPopular — returns sorted by downloads", () => {
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, name: "low-skill" }, downloads: 10 }));
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, name: "high-skill" }, downloads: 100 }));
    const popular = registry.getPopular(5);
    expect(popular[0].downloads).toBeGreaterThanOrEqual(popular[1].downloads);
  });

  it("getByTag — filters by tag", () => {
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, name: "tagged-skill", tags: ["ai", "utility"] } }));
    registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, name: "other-skill", tags: ["cli"] } }));
    const results = registry.getByTag("ai");
    expect(results.every((p) => p.manifest.tags.includes("ai"))).toBe(true);
    expect(results.find((p) => p.manifest.name === "other-skill")).toBeUndefined();
  });

  it("listAll — paginates with limit and offset", () => {
    for (let i = 0; i < 5; i++) {
      registry.publish(createTestPackage({ manifest: { ...createTestPackage().manifest, name: `skill-${i}` } }));
    }
    const page1 = registry.listAll({ limit: 2, offset: 0 });
    const page2 = registry.listAll({ limit: 2, offset: 2 });
    expect(page1).toHaveLength(2);
    expect(page2).toHaveLength(2);
    // Pages should not overlap
    expect(page1[0].manifest.name).not.toBe(page2[0].manifest.name);
  });
});
