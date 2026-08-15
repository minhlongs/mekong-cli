/**
 * Portfolio — list, detail, and compare ventures across the workspace.
 */

import { readFileSync, existsSync, readdirSync } from 'fs';
import { join, basename } from 'path';
import { parseToml } from './venture-toml-parser.ts';

export interface VentureSummary {
  id: string;
  name: string;
  type: string;
  phase: string;
  phaseLabel: string;
  status: string;
  updatedAt: string;
  decisionsCount: number;
  eventsCount: number;
}

export interface VentureDetail extends VentureSummary {
  tomlPath: string;
  statePath: string;
  decisionsDir: string;
  artifactsDir: string;
  decisions: Array<{ id: string; title: string; type: string; decidedAt?: string }>;
  recentEvents: Array<{ type: string; timestamp: string }>;
  gatesPassed: string[];
}

export interface VentureComparison {
  ventures: VentureSummary[];
  comparedAt: string;
  dimensions: string[];
}

/**
 * Scan the ventures/ directory and return summaries for all ventures.
 */
export function listVentures(venturesRoot: string = join('.', 'ventures')): VentureSummary[] {
  if (!existsSync(venturesRoot)) return [];

  return readdirSync(venturesRoot)
    .filter((d) => {
      const full = join(venturesRoot, d);
      return existsSync(join(full, 'venture.toml')) && existsSync(join(full, 'state.json'));
    })
    .map((id) => {
      const dir = join(venturesRoot, id);
      const summary = summarizeVenture(dir, id);
      return summary;
    })
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

/**
 * Get full detail for a single venture.
 */
export function getVentureDetail(venturesRoot: string, ventureId: string): VentureDetail | null {
  const dir = join(venturesRoot, ventureId);
  const tomlPath = join(dir, 'venture.toml');
  const statePath = join(dir, 'state.json');

  if (!existsSync(tomlPath) || !existsSync(statePath)) return null;

  const summary = summarizeVenture(dir, ventureId);

  // Load recent decisions
  const decisionsDir = join(dir, 'decisions');
  const decisions: VentureDetail['decisions'] = [];
  if (existsSync(decisionsDir)) {
    for (const f of readdirSync(decisionsDir).filter((f) => f.endsWith('.md')).slice(-5)) {
      const content = readFileSync(join(decisionsDir, f), 'utf-8');
      const idMatch = f.match(/^(.+)\.md$/);
      const titleMatch = content.match(/^#\s+(.+)/m);
      const typeMatch = content.match(/type:\s*(\w+)/);
      decisions.push({
        id: idMatch?.[1] ?? f,
        title: titleMatch?.[1] ?? 'Untitled',
        type: typeMatch?.[1] ?? 'unknown',
      });
    }
  }

  // Load recent events from WAL
  const waldir = join(dir, 'wal');
  const recentEvents: VentureDetail['recentEvents'] = [];
  if (existsSync(waldir)) {
    const files = readdirSync(waldir)
      .filter((f) => f.endsWith('.jsonl'))
      .sort()
      .slice(-1);
    for (const f of files) {
      const lines = readFileSync(join(waldir, f), 'utf-8')
        .split('\n')
        .filter(Boolean)
        .slice(-10);
      for (const line of lines) {
        try {
          const ev = JSON.parse(line);
          recentEvents.push({
            type: ev.type ?? 'unknown',
            timestamp: ev.timestamp ?? '',
          });
        } catch {
          // skip
        }
      }
    }
  }

  return {
    ...summary,
    tomlPath,
    statePath,
    decisionsDir,
    artifactsDir: join(dir, 'artifacts'),
    decisions,
    recentEvents,
    gatesPassed: [], // populated from state if available
  };
}

/**
 * Compare multiple ventures by ID, returning a structured comparison.
 */
export function compareVentures(
  venturesRoot: string,
  ids: string[],
): VentureComparison | null {
  const summaries = ids
    .map((id) => {
      const detail = getVentureDetail(venturesRoot, id);
      if (!detail) return null;
      return {
        id: detail.id,
        name: detail.name,
        type: detail.type,
        phase: detail.phase,
        phaseLabel: detail.phaseLabel,
        status: detail.status,
        updatedAt: detail.updatedAt,
        decisionsCount: detail.decisions.length,
        eventsCount: detail.recentEvents.length,
      } as VentureSummary;
    })
    .filter(Boolean) as VentureSummary[];

  if (summaries.length === 0) return null;

  return {
    ventures: summaries,
    comparedAt: new Date().toISOString(),
    dimensions: ['name', 'type', 'phase', 'status', 'decisionsCount', 'eventsCount'],
  };
}

// ─── Internal Helpers ─────────────────────────────────────────────────────────

function summarizeVenture(dir: string, id: string): VentureSummary {
  const tomlPath = join(dir, 'venture.toml');
  const statePath = join(dir, 'state.json');

  let name = id;
  let type = 'unknown';

  if (existsSync(tomlPath)) {
    try {
      const parsed = parseToml(readFileSync(tomlPath, 'utf-8'));
      const inner = typeof parsed.id === 'object' && parsed.id !== null
        ? (parsed.id as Record<string, string>)
        : parsed as Record<string, string>;
      name = inner.name ?? id;
      type = inner.type ?? 'unknown';
    } catch {
      // use defaults
    }
  }

  let phase = '01';
  let phaseLabel = 'IDENTIFY';
  let status = 'active';
  let updatedAt = '';
  let decisionsCount = 0;
  let eventsCount = 0;

  if (existsSync(statePath)) {
    try {
      const state = JSON.parse(readFileSync(statePath, 'utf-8'));
      phase = state.current_phase ?? phase;
      phaseLabel = state.phase_label ?? phaseLabel;
      status = state.status ?? status;
      updatedAt = state.updated_at ?? '';
      decisionsCount = state.decisions_count ?? 0;
      eventsCount = state.events_count ?? 0;
    } catch {
      // use defaults
    }
  }

  return { id, name, type, phase, phaseLabel, status, updatedAt, decisionsCount, eventsCount };
}
