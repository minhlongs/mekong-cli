/**
 * API Versioning Service — version negotiation, changelog, usage tracking
 *
 * Supported versions: v1 (current), v2 (deprecated)
 * Priority: path prefix > X-API-Version header > default 'v1'
 */

import type { D1Database } from '@cloudflare/workers-types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface APIVersion {
  version: string;
  status: 'current' | 'deprecated' | 'sunset';
  released_at: string;
  sunset_at: string | null;
  changelog: string;
}

export interface VersionNegotiation {
  requested: string;
  resolved: string;
  source: 'path' | 'header' | 'default';
  warnings: string[];
}

export interface ChangelogEntry {
  id: string;
  version: string;
  title: string;
  description: string | null;
  change_type: string;
  created_at: string;
}

export interface VersionUsageStat {
  version: string;
  request_count: number;
  unique_tenants: number;
}

// ---------------------------------------------------------------------------
// Static registry
// ---------------------------------------------------------------------------

const VERSIONS: APIVersion[] = [
  { version: 'v1', status: 'current', released_at: '2025-01-01', sunset_at: null, changelog: 'Initial stable release' },
  { version: 'v2', status: 'deprecated', released_at: '2025-06-01', sunset_at: '2026-12-31', changelog: 'Beta — deprecated, use v1' },
];

const SUPPORTED = new Set(VERSIONS.map((v) => v.version));

const MIGRATION_GUIDES: Record<string, string[]> = {
  'v1->v2': ['Update base URL from /v1/ to /v2/', 'Bearer tokens remain compatible', 'Response envelope unchanged'],
  'v2->v1': ['v2 is deprecated — migrate back to v1', 'Replace /v2/ prefix with /v1/', 'No API contract changes required'],
};

// ---------------------------------------------------------------------------
// Version negotiation
// ---------------------------------------------------------------------------

export function negotiateVersion(path: string, headers: Headers): VersionNegotiation {
  const warnings: string[] = [];

  const pathMatch = path.match(/^\/(v\d+)\//);
  if (pathMatch) {
    const ver = pathMatch[1];
    if (SUPPORTED.has(ver)) {
      const info = VERSIONS.find((v) => v.version === ver)!;
      if (info.status !== 'current') warnings.push(`Version ${ver} is ${info.status}. Sunset: ${info.sunset_at}`);
      return { requested: ver, resolved: ver, source: 'path', warnings };
    }
  }

  const headerVer = headers.get('X-API-Version');
  if (headerVer && SUPPORTED.has(headerVer)) {
    const info = VERSIONS.find((v) => v.version === headerVer)!;
    if (info.status !== 'current') warnings.push(`Version ${headerVer} is ${info.status}. Sunset: ${info.sunset_at}`);
    return { requested: headerVer, resolved: headerVer, source: 'header', warnings };
  }

  return { requested: 'v1', resolved: 'v1', source: 'default', warnings };
}

export const getVersionInfo = (): APIVersion[] => VERSIONS;
export const isVersionSupported = (v: string): boolean => SUPPORTED.has(v);

export function getDeprecationWarnings(version: string): string[] {
  const info = VERSIONS.find((v) => v.version === version);
  if (!info) return [`Version ${version} is not recognized.`];
  if (info.status !== 'current') return [`Version ${version} is ${info.status}. Sunset: ${info.sunset_at}`];
  return [];
}

export function getMigrationGuide(fromVersion: string, toVersion: string): string[] {
  return MIGRATION_GUIDES[`${fromVersion}->${toVersion}`] ?? [`No migration guide available from ${fromVersion} to ${toVersion}.`];
}

// ---------------------------------------------------------------------------
// D1 — Changelog
// ---------------------------------------------------------------------------

export async function getVersionChangelog(db: D1Database, version: string): Promise<ChangelogEntry[]> {
  const r = await db.prepare('SELECT * FROM api_version_changelog WHERE version = ? ORDER BY created_at DESC').bind(version).all<ChangelogEntry>();
  return r.results ?? [];
}

export async function addChangelogEntry(
  db: D1Database, version: string, title: string, description: string,
  type: 'added' | 'changed' | 'deprecated' | 'removed',
): Promise<ChangelogEntry> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare('INSERT INTO api_version_changelog (id, version, title, description, change_type, created_at) VALUES (?, ?, ?, ?, ?, ?)')
    .bind(id, version, title, description, type, now).run();
  return { id, version, title, description, change_type: type, created_at: now };
}

// ---------------------------------------------------------------------------
// D1 — Usage
// ---------------------------------------------------------------------------

export async function recordVersionUsage(db: D1Database, tenantId: string, version: string, endpoint: string): Promise<void> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare('INSERT INTO api_version_usage (id, tenant_id, api_version, endpoint, created_at) VALUES (?, ?, ?, ?, ?)')
    .bind(id, tenantId, version, endpoint, now).run();
}

export async function getVersionUsageStats(db: D1Database, days = 30): Promise<VersionUsageStat[]> {
  const since = new Date(Date.now() - days * 86400_000).toISOString();
  const r = await db.prepare(
    `SELECT api_version AS version, COUNT(*) AS request_count, COUNT(DISTINCT tenant_id) AS unique_tenants
     FROM api_version_usage WHERE created_at >= ? GROUP BY api_version ORDER BY request_count DESC`,
  ).bind(since).all<VersionUsageStat>();
  return r.results ?? [];
}
