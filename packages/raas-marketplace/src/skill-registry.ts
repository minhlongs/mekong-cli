// In-memory skill registry for the Mekong CLI marketplace (MVP).
// Will be backed by Cloudflare D1 in a future iteration.

import type { SkillPackage } from "./skill-package.js";
import { validateManifest } from "./skill-package.js";

export interface SearchOptions {
  tag?: string;
  author?: string;
  limit?: number;
  sortBy?: "downloads" | "rating" | "newest";
}

export interface ListOptions {
  limit?: number;
  offset?: number;
  sortBy?: "downloads" | "rating" | "newest" | "name";
}

// ---------------------------------------------------------------------------
// Scoring helpers for relevance-ranked search
// ---------------------------------------------------------------------------

function matchScore(pkg: SkillPackage, query: string): number {
  const q = query.toLowerCase();
  let score = 0;

  // Name match is highest signal
  if (pkg.manifest.name === q) score += 10;
  else if (pkg.manifest.name.includes(q)) score += 6;

  // Description match is secondary
  if (pkg.manifest.description.toLowerCase().includes(q)) score += 3;

  // Tag match is tertiary
  if (pkg.manifest.tags.some((t) => t.toLowerCase().includes(q))) score += 2;

  return score;
}

function applySortBy<T extends SkillPackage>(
  pkgs: T[],
  sortBy: "downloads" | "rating" | "newest" | "name" | undefined
): T[] {
  if (!sortBy) return pkgs;
  return [...pkgs].sort((a, b) => {
    switch (sortBy) {
      case "downloads":
        return b.downloads - a.downloads;
      case "rating":
        return b.rating - a.rating;
      case "newest":
        return b.publishedAt.getTime() - a.publishedAt.getTime();
      case "name":
        return a.manifest.name.localeCompare(b.manifest.name);
    }
  });
}

// ---------------------------------------------------------------------------
// SkillRegistry
// ---------------------------------------------------------------------------

/** In-memory registry that stores skill packages grouped by name. */
export class SkillRegistry {
  // name → ordered list of versions (newest last)
  private skills: Map<string, SkillPackage[]> = new Map();

  /**
   * Publish a skill package.
   * Validates the manifest and rejects duplicate name@version entries.
   */
  publish(pkg: SkillPackage): { success: boolean; error?: string } {
    const { valid, errors } = validateManifest(pkg.manifest);
    if (!valid) {
      return { success: false, error: errors.join("; ") };
    }

    const { name, version } = pkg.manifest;
    const versions = this.skills.get(name) ?? [];

    if (versions.some((p) => p.manifest.version === version)) {
      return { success: false, error: `${name}@${version} already exists` };
    }

    this.skills.set(name, [...versions, pkg]);
    return { success: true };
  }

  /**
   * Search skills by query string (name / description / tags).
   * Filters by tag and author when provided; sorts by relevance then by option.
   */
  search(query: string, options: SearchOptions = {}): SkillPackage[] {
    const { tag, author, limit = 20, sortBy } = options;
    const q = query.toLowerCase().trim();

    let candidates = this.listAll({ sortBy });

    if (tag) {
      candidates = candidates.filter((p) =>
        p.manifest.tags.some((t) => t.toLowerCase() === tag.toLowerCase())
      );
    }

    if (author) {
      candidates = candidates.filter(
        (p) =>
          p.manifest.author.toLowerCase() === author.toLowerCase()
      );
    }

    if (q) {
      candidates = candidates
        .map((p) => ({ pkg: p, score: matchScore(p, q) }))
        .filter(({ score }) => score > 0)
        .sort((a, b) => b.score - a.score)
        .map(({ pkg }) => pkg);
    }

    return candidates.slice(0, limit);
  }

  /** Returns the latest (last published) version of a skill by name. */
  getLatest(name: string): SkillPackage | undefined {
    const versions = this.skills.get(name);
    return versions?.[versions.length - 1];
  }

  /** Returns a specific version of a skill. */
  getVersion(name: string, version: string): SkillPackage | undefined {
    return this.skills
      .get(name)
      ?.find((p) => p.manifest.version === version);
  }

  /** Lists all latest-version packages with optional sorting and pagination. */
  listAll(options: ListOptions = {}): SkillPackage[] {
    const { limit, offset = 0, sortBy } = options;

    // One entry per skill name: the latest version
    const latest = Array.from(this.skills.values()).map(
      (versions) => versions[versions.length - 1]
    );

    const sorted = applySortBy(latest, sortBy);
    return limit !== undefined
      ? sorted.slice(offset, offset + limit)
      : sorted.slice(offset);
  }

  /**
   * Records a rating for a skill (1–5).
   * Updates running average and count. Returns false for invalid input.
   */
  rate(name: string, rating: number): boolean {
    if (rating < 1 || rating > 5 || !Number.isFinite(rating)) return false;

    const versions = this.skills.get(name);
    if (!versions || versions.length === 0) return false;

    // Update all versions to share the same rating stats
    for (const pkg of versions) {
      const total = pkg.rating * pkg.ratingCount + rating;
      pkg.ratingCount += 1;
      pkg.rating = total / pkg.ratingCount;
    }
    return true;
  }

  /** Returns the most-downloaded skills (default top 10). */
  getPopular(limit = 10): SkillPackage[] {
    return this.listAll({ sortBy: "downloads", limit });
  }

  /** Returns all latest-version packages that include the given tag. */
  getByTag(tag: string): SkillPackage[] {
    return this.listAll().filter((p) =>
      p.manifest.tags.some((t) => t.toLowerCase() === tag.toLowerCase())
    );
  }
}
