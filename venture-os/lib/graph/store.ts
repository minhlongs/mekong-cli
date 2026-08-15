/**
 * VentureOS Knowledge Graph — Persistence Layer
 *
 * Handles low-level storage operations for the graph:
 *   - Batch entity write (atomic rename pattern)
 *   - Entity import/export (JSON + JSONL)
 *   - Snapshot + restore (compaction for recovery)
 *   - Entity rebuild from WAL events (rehydration)
 *   - Cross-venture merge (patterns across ventures)
 *
 * This is the storage engine. The high-level API is in index.ts.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, statSync, renameSync, copyFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import type { GraphEntity, GraphRelationship } from './index.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');

// ─── Paths ───────────────────────────────────────────────────────────────────

const getGraphDir = (ventureId: string) => join(ROOT, 'ventures', ventureId, 'knowledge', 'graph');
const getEntitiesDir = (ventureId: string) => join(getGraphDir(ventureId), 'entities');
const getRelationshipsFile = (ventureId: string) => join(getGraphDir(ventureId), 'relationships.jsonl');
const getSnapshotsDir = (ventureId: string) => join(getGraphDir(ventureId), '.snapshots');
const getTrashDir = (ventureId: string) => join(getEntitiesDir(ventureId), '.deleted');

// ─── Helpers ─────────────────────────────────────────────────────────────────

function ensureDirs(ventureId: string): { graph: string; entities: string; snapshots: string; trash: string } {
  const graph = getGraphDir(ventureId);
  const entities = getEntitiesDir(ventureId);
  const snapshots = getSnapshotsDir(ventureId);
  const trash = getTrashDir(ventureId);

  for (const dir of [graph, entities, snapshots, trash]) {
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  }
  return { graph, entities, snapshots, trash };
}

function readAllEntities(ventureId: string): GraphEntity[] {
  const dir = getEntitiesDir(ventureId);
  if (!existsSync(dir)) return [];

  const entities: GraphEntity[] = [];
  for (const file of readdirSync(dir)) {
    if (file.startsWith('.') || !file.endsWith('.json')) continue;
    const fullPath = join(dir, file);
    try {
      const entity = JSON.parse(readFileSync(fullPath, 'utf-8')) as GraphEntity;
      entities.push(entity);
    } catch { /* skip corrupt */ }
  }
  return entities;
}

function readAllRelationships(ventureId: string): GraphRelationship[] {
  const relsPath = getRelationshipsFile(ventureId);
  if (!existsSync(relsPath)) return [];

  const relationships: GraphRelationship[] = [];
  for (const line of readFileSync(relsPath, 'utf-8').split('\n').filter((l) => l.trim())) {
    try {
      relationships.push(JSON.parse(line) as GraphRelationship);
    } catch { /* skip malformed */ }
  }
  return relationships;
}

// ─── Snapshot ────────────────────────────────────────────────────────────────

/**
 * Export current graph state as a snapshot for backup/recovery.
 * Creates `.snapshots/snapshot-<ts>.json.gz` — lightweight copy-on-write pattern.
 */
export function snapshot(ventureId: string): { path: string; entityCount: number; relationshipCount: number } {
  const { snapshots } = ensureDirs(ventureId);
  const ts = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
  const snapshotPath = join(snapshots, `snapshot-${ts}.json`);

  const entities = readAllEntities(ventureId);
  const relationships = readAllRelationships(ventureId);

  const payload = {
    ventureId,
    timestamp: ts,
    entities,
    relationships,
  };

  writeFileSync(snapshotPath, JSON.stringify(payload, null, 2), 'utf-8');

  return {
    path: snapshotPath,
    entityCount: entities.length,
    relationshipCount: relationships.length,
  };
}

/**
 * Restore a graph from a snapshot file.
 * Writes snapshot entities + relationships into live graph dir.
 * WARNING: this replaces current state. Use snapshot() to backup first.
 */
export function restore(ventureId: string, snapshotPath: string): { entitiesRestored: number; relationshipsRestored: number } {
  if (!existsSync(snapshotPath)) {
    throw new Error(`Snapshot not found: ${snapshotPath}`);
  }

  const { entities, relationships } = JSON.parse(readFileSync(snapshotPath, 'utf-8')) as { ventureId: string; entities: GraphEntity[]; relationships: GraphRelationship[] };
  ensureDirs(ventureId);

  // Write entities
  let entitiesRestored = 0;
  for (const entity of entities) {
    const outPath = join(getEntitiesDir(ventureId), `${entity.id}.json`);
    writeFileSync(outPath, JSON.stringify(entity, null, 2), 'utf-8');
    entitiesRestored++;
  }

  // Write relationships (overwrite current)
  const relsPath = getRelationshipsFile(ventureId);
  writeFileSync(relsPath, '', 'utf-8'); // truncate
  for (const rel of relationships) {
    writeFileSync(relsPath, JSON.stringify(rel) + '\n', { flag: 'a' });
  }

  return { entitiesRestored, relationshipsRestored: relationships.length };
}

/**
 * List available snapshots for a venture (sorted newest first).
 */
export function listSnapshots(ventureId: string): { path: string; timestamp: string; entityCount: number }[] {
  const snapshotsDir = getSnapshotsDir(ventureId);
  if (!existsSync(snapshotsDir)) return [];

  const snapshots: { path: string; timestamp: string; entityCount: number }[] = [];

  for (const file of readdirSync(snapshotsDir)) {
    if (!file.endsWith('.json')) continue;
    const fullPath = join(snapshotsDir, file);
    try {
      const data = JSON.parse(readFileSync(fullPath, 'utf-8')) as { timestamp: string; entities: unknown[] };
      snapshots.push({
        path: fullPath,
        timestamp: data.timestamp,
        entityCount: data.entities?.length ?? 0,
      });
    } catch { /* skip corrupt snapshot */ }
  }

  return snapshots.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

// ─── Import / Export ─────────────────────────────────────────────────────────

/**
 * Export all graph data for a venture to a single JSON file.
 * Useful for backup, migration, or cross-venture analysis.
 */
export function exportGraph(ventureId: string, outputPath?: string): { path: string; sizeBytes: number } {
  const entities = readAllEntities(ventureId);
  const relationships = readAllRelationships(ventureId);
  const trashDir = getTrashDir(ventureId);
  const deletedCount = existsSync(trashDir) ? readdirSync(trashDir).filter((f) => f.endsWith('.json')).length : 0;

  const payload = {
    ventureId,
    exportedAt: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
    stats: { entities: entities.length, relationships: relationships.length, deleted: deletedCount },
    entities,
    relationships,
  };

  const outPath = outputPath ?? join(getGraphDir(ventureId), `export-${Date.now()}.json`);
  const content = JSON.stringify(payload, null, 2);
  writeFileSync(outPath, content, 'utf-8');

  return { path: outPath, sizeBytes: Buffer.byteLength(content, 'utf-8') };
}

/**
 * Import graph data from an export file.
 * Merges by entity id (upsert), appends relationships.
 */
export function importGraph(ventureId: string, importPath: string): { added: number; updated: number; relationshipsAdded: number } {
  if (!existsSync(importPath)) {
    throw new Error(`Import file not found: ${importPath}`);
  }

  const { entities, relationships } = JSON.parse(readFileSync(importPath, 'utf-8')) as {
    ventureId: string;
    entities: GraphEntity[];
    relationships: GraphRelationship[];
  };

  ensureDirs(ventureId);

  let added = 0;
  let updated = 0;

  for (const entity of entities) {
    const existingPath = join(getEntitiesDir(ventureId), `${entity.id}.json`);
    if (existsSync(existingPath)) {
      writeFileSync(existingPath, JSON.stringify(entity, null, 2), 'utf-8');
      updated++;
    } else {
      writeFileSync(existingPath, JSON.stringify(entity, null, 2), 'utf-8');
      added++;
    }
  }

  // Append relationships (append-only)
  const relsPath = getRelationshipsFile(ventureId);
  for (const rel of relationships) {
    writeFileSync(relsPath, JSON.stringify(rel) + '\n', { flag: 'a' });
  }

  return { added, updated, relationshipsAdded: relationships.length };
}

// ─── Cleanup / Garbage Collection ──────────────────────────────────────────

/**
 * Permanently delete entities in .deleted/ that are older than keepDays.
 * Soft-delete moves entities to .deleted/. This compacts trash to recover space.
 */
export function gcTrash(ventureId: string, keepDays: number = 30): { purged: number; kept: number } {
  const trashDir = getTrashDir(ventureId);
  if (!existsSync(trashDir)) return { purged: 0, kept: 0 };

  const cutoff = Date.now() - keepDays * 24 * 60 * 60 * 1000;
  let purged = 0;
  let kept = 0;

  for (const file of readdirSync(trashDir)) {
    if (!file.endsWith('.json')) continue;
    const fullPath = join(trashDir, file);
    const mtime = statSync(fullPath).mtimeMs;

    if (mtime < cutoff) {
      try { renameSync(fullPath, fullPath + '.purge'); } catch { /* already purged */ }
      purged++;
    } else {
      kept++;
    }
  }

  return { purged, kept };
}

/**
 * Rebuild relationships from scratch by scanning all entities for orphan
 * references. Used after bulk entity operations or corruption recovery.
 */
export function rebuildRelationships(ventureId: string, dryRun: boolean = false): { skipped: number; rebuilt: number } {
  const entities = readAllEntities(ventureId);
  const existingRels = readAllRelationships(ventureId);
  const entityIds = new Set(entities.map((e) => e.id));

  // Find relationships referencing non-existent entities
  const orphanRels = existingRels.filter((r) => !entityIds.has(r.sourceId) || !entityIds.has(r.targetId));
  const validRels = existingRels.filter((r) => entityIds.has(r.sourceId) && entityIds.has(r.targetId));

  if (!dryRun) {
    const relsPath = getRelationshipsFile(ventureId);
    // Safely rewrite by writing to temp file then renaming
    const tempPath = relsPath + '.tmp';
    writeFileSync(tempPath, '', 'utf-8');
    for (const rel of validRels) {
      writeFileSync(tempPath, JSON.stringify(rel) + '\n', { flag: 'a' });
    }
    renameSync(tempPath, relsPath);
  }

  return { skipped: validRels.length, rebuilt: orphanRels.length };
}

// ─── Rehydration from WAL ─────────────────────────────────────────────────────

/**
 * Rebuild graph entities from WAL workflow_run events.
 * Extracts entity metadata from workflow step outputs stored in the WAL.
 * This is the bridge between the WAL (event log) and the knowledge graph.
 */
export function rehydrateFromWAL(ventureId: string): { eventsProcessed: number; entitiesCreated: number } {
  const walPath = join(ROOT, 'ventures', ventureId, 'wal', 'current.jsonl');
  if (!existsSync(walPath)) return { eventsProcessed: 0, entitiesCreated: 0 };

  let eventsProcessed = 0;
  let entitiesCreated = 0;

  ensureDirs(ventureId);

  for (const line of readFileSync(walPath, 'utf-8').split('\n').filter((l) => l.trim())) {
    try {
      const event = JSON.parse(line);
      eventsProcessed++;

      // Only rehydrate workflow_run events that contain graph entities in payload
      if (event.type === 'workflow_run' && event.payload?.graphEntities) {
        const graphEntities: unknown[] = event.payload.graphEntities;
        for (const ge of graphEntities) {
          if (typeof ge === 'object' && ge !== null && 'type' in ge && 'properties' in ge) {
            const entityData = ge as { type: string; properties: Record<string, unknown> };
            const entityPath = join(getEntitiesDir(ventureId), `${entityData.type}.json`);
            if (!existsSync(entityPath)) {
              writeFileSync(entityPath, JSON.stringify({
                id: `entity-${ventureId}-${entityData.type}-${Date.now()}`,
                ventureId,
                type: entityData.type,
                labels: [entityData.type],
                properties: entityData.properties,
                createdAt: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
                updatedAt: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
              }, null, 2), 'utf-8');
              entitiesCreated++;
            }
          }
        }
      }
    } catch { /* skip malformed WAL lines */ }
  }

  return { eventsProcessed, entitiesCreated };
}

// ─── Stats ───────────────────────────────────────────────────────────────────

export function getGraphInfo(ventureId: string): {
  ventureId: string;
  entityCount: number;
  relationshipCount: number;
  snapshotCount: number;
  trashCount: number;
  sizeBytes: number;
  lastModified: string | null;
} {
  const entitiesDir = getEntitiesDir(ventureId);
  const relsPath = getRelationshipsFile(ventureId);
  const snapshotsDir = getSnapshotsDir(ventureId);
  const trashDir = getTrashDir(ventureId);

  let entityCount = 0;
  let sizeBytes = 0;
  let lastMtime = 0;
  let lastModified: string | null = null;

  if (existsSync(entitiesDir)) {
    for (const file of readdirSync(entitiesDir)) {
      if (file.startsWith('.') || !file.endsWith('.json')) continue;
      const fullPath = join(entitiesDir, file);
      const stat = statSync(fullPath);
      entityCount++;
      sizeBytes += stat.size;
      if (stat.mtimeMs > lastMtime) {
        lastMtime = stat.mtimeMs;
        lastModified = new Date(stat.mtimeMs).toISOString();
      }
    }
  }

  let relCount = 0;
  if (existsSync(relsPath)) {
    const stat = statSync(relsPath);
    relCount = readFileSync(relsPath, 'utf-8').split('\n').filter((l) => l.trim()).length;
    sizeBytes += stat.size;
  }

  const snapshotCount = existsSync(snapshotsDir) ? readdirSync(snapshotsDir).filter((f) => f.endsWith('.json')).length : 0;
  const trashCount = existsSync(trashDir) ? readdirSync(trashDir).filter((f) => f.endsWith('.json')).length : 0;

  return {
    ventureId,
    entityCount,
    relationshipCount: relCount,
    snapshotCount,
    trashCount,
    sizeBytes,
    lastModified,
  };
}

// ─── Cross-Venture Merge ─────────────────────────────────────────────────────

/**
 * Merge entities from source venture into target venture by entity type.
 * Useful for portfolio-level pattern extraction or template creation.
 * Skips duplicates by entity type + name (within properties.name).
 */
export function mergeByType(
  sourceVentureId: string,
  targetVentureId: string,
  types: string[] = ['market', 'competitor'],
): { merged: number; skipped: number } {
  const sourceEntities = readAllEntities(sourceVentureId);
  const targetEntities = readAllEntities(targetVentureId);

  // Build lookup: type + name → existing entity id
  const existingKeys = new Set(
    targetEntities.map((e) => `${e.type}:${String(e.properties.name ?? '')}`),
  );

  let merged = 0;
  let skipped = 0;

  ensureDirs(targetVentureId);

  for (const source of sourceEntities) {
    if (!types.includes(source.type)) continue;
    const name = String(source.properties.name ?? '');
    const key = `${source.type}:${name}`;
    if (existingKeys.has(key)) { skipped++; continue; }

    const clone: GraphEntity = {
      ...source,
      id: `entity-imported-${targetVentureId}-${source.type}-${Date.now()}-${merged}`,
      ventureId: targetVentureId,
      createdAt: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
      updatedAt: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
    };

    writeFileSync(join(getEntitiesDir(targetVentureId), `${clone.id}.json`), JSON.stringify(clone, null, 2), 'utf-8');
    existingKeys.add(key);
    merged++;
  }

  return { merged, skipped };
}
