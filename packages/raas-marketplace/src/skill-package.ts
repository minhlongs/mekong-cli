// Skill package format for the Mekong CLI marketplace.
// Defines the manifest schema, package structure, and validation helpers.

/** Metadata describing a publishable skill. */
export interface SkillManifest {
  name: string; // kebab-case, e.g. "react-best-practices"
  version: string; // semver e.g. "1.0.0"
  description: string;
  author: string;
  license: string;
  tags: string[];
  triggers: string[]; // activation keywords / events
  dependencies?: string[]; // other skill names this depends on
  minCliVersion?: string; // minimum mekong-cli version required
}

/** A published skill package with metadata and content. */
export interface SkillPackage {
  manifest: SkillManifest;
  readme: string; // SKILL.md content
  files: SkillFile[]; // scripts, references, templates
  signature?: string; // Ed25519 signature for verification
  publishedAt: Date;
  downloads: number;
  rating: number; // 0–5 average
  ratingCount: number;
}

/** A single file bundled inside a skill package. */
export interface SkillFile {
  path: string; // relative path within the package
  content: string;
  size: number; // bytes
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

const SEMVER_RE = /^\d+\.\d+\.\d+(?:-[\w.]+)?(?:\+[\w.]+)?$/;
const NAME_RE = /^[a-z][a-z0-9-]{1,48}[a-z0-9]$/; // 3–50 chars, kebab-case

/**
 * Validates a SkillManifest against required-field and format rules.
 * Returns `{ valid: true }` or `{ valid: false, errors: [...] }`.
 */
export function validateManifest(
  manifest: SkillManifest
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!manifest.name) {
    errors.push("name is required");
  } else if (!NAME_RE.test(manifest.name)) {
    errors.push(
      "name must be kebab-case, 3–50 characters (lowercase letters, digits, hyphens)"
    );
  }

  if (!manifest.version) {
    errors.push("version is required");
  } else if (!SEMVER_RE.test(manifest.version)) {
    errors.push("version must be valid semver (e.g. 1.0.0)");
  }

  if (!manifest.description || manifest.description.trim().length === 0) {
    errors.push("description is required");
  }

  if (!manifest.author || manifest.author.trim().length === 0) {
    errors.push("author is required");
  }

  if (!manifest.license || manifest.license.trim().length === 0) {
    errors.push("license is required");
  }

  if (!Array.isArray(manifest.tags)) {
    errors.push("tags must be an array");
  }

  if (!Array.isArray(manifest.triggers)) {
    errors.push("triggers must be an array");
  }

  return { valid: errors.length === 0, errors };
}

/** Returns a canonical package identifier: `name@version`. */
export function createPackageId(name: string, version: string): string {
  return `${name}@${version}`;
}

/**
 * Parses a package ID string (`name@version`) back into its components.
 * Returns `null` when the format is invalid.
 */
export function parsePackageId(
  id: string
): { name: string; version: string } | null {
  const atIndex = id.lastIndexOf("@");
  if (atIndex <= 0) return null;

  const name = id.slice(0, atIndex);
  const version = id.slice(atIndex + 1);

  if (!name || !version) return null;
  return { name, version };
}
