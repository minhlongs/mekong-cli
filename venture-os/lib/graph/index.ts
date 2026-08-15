/**
 * VentureOS Knowledge Graph Public API
 *
 * The knowledge graph is the universal substrate (ADR-010).
 * It stores entities (nodes) and relationships (edges) for a venture,
 * enabling cross-venture intelligence, pattern detection, and traceability.
 *
 * Entities: ventures, decisions, milestones, markets, competitors, products, people
 * Relationships: depends_on, leads_to, competes_with, targets, includes, ...
 *
 * Storage: JSON files per entity under ventures/{id}/knowledge/graph/entities/
 *          JSONL for relationships (append-only).
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, statSync, renameSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');

// ─── Types ───────────────────────────────────────────────────────────────────

export interface GraphEntity {
  id: string;                  // e.g. "entity-<venture-id>-<slug>-<YYYYMMDD>"
  ventureId: string;
  type: EntityType;
  labels: string[];            // e.g. ["market", "ai", "target"]
  properties: Record<string, unknown>;
  createdAt: string;           // ISO-8601
  updatedAt: string;
}

export interface GraphRelationship {
  id: string;                  // e.g. "rel-<venture-id>-<hash>"
  ventureId: string;
  type: string;                // e.g. "depends_on", "leads_to", "competes_with"
  sourceId: string;            // entity id
  targetId: string;            // entity id
  properties: Record<string, unknown>;
  createdAt: string;
}

export interface GraphQuery {
  ventureId?: string;
  type?: string;               // entity type filter
  label?: string;              // label filter (match any)
  sourceId?: string;           // outgoing from this entity
  targetId?: string;           // incoming to this entity
  limit?: number;
}

export interface GraphQueryResult {
  entities: GraphEntity[];
  relationships: GraphRelationship[];
  totalFound: number;
}

export interface GraphStats {
  entityCount: number;
  relationshipCount: number;
  entityTypes: Record<string, number>;
  relationshipTypes: Record<string, number>;
}

export type EntityType =
  | 'venture'
  | 'decision'
  | 'milestone'
  | 'market'
  | 'competitor'
  | 'product'
  | 'person'
  | 'insight'
  | 'risk'
  | 'asset';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const GRAPH_DIR_PATTERN = (ventureId: string) => join(ROOT, 'ventures', ventureId, 'knowledge', 'graph');
const ENTITIES_DIR = (ventureId: string) => join(GRAPH_DIR_PATTERN(ventureId), 'entities');
const RELATIONSHIPS_FILE = (ventureId: string) => join(GRAPH_DIR_PATTERN(ventureId), 'relationships.jsonl');

function ensureGraphDir(ventureId: string): void {
  const dir = ENTITIES_DIR(ventureId);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function entityPath(ventureId: string, entityId: string): string {
  return join(ENTITIES_DIR(ventureId), `${entityId}.json`);
}

function relationshipPath(ventureId: string): string {
  return RELATIONSHIPS_FILE(ventureId);
}

function generateId(prefix: string, ventureId: string, slug?: string): string {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').slice(0, 16);
  const s = slug ? `-${slug}` : '';
  return `${prefix}-${ventureId}${s}-${ts}`;
}

// ─── Entity CRUD ─────────────────────────────────────────────────────────────

export function addEntity(
  ventureId: string,
  entity: Omit<GraphEntity, 'id' | 'createdAt' | 'updatedAt'>,
): GraphEntity {
  ensureGraphDir(ventureId);
  const now = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
  const slug = entity.properties?.name
    ? String(entity.properties.name).toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30)
    : undefined;

  const fullEntity: GraphEntity = {
    ...entity,
    id: generateId('entity', ventureId, slug),
    createdAt: now,
    updatedAt: now,
  };

  writeFileSync(entityPath(ventureId, fullEntity.id), JSON.stringify(fullEntity, null, 2), 'utf-8');
  return fullEntity;
}

export function getEntity(ventureId: string, entityId: string): GraphEntity | undefined {
  const path = entityPath(ventureId, entityId);
  if (!existsSync(path)) return undefined;
  try {
    return JSON.parse(readFileSync(path, 'utf-8')) as GraphEntity;
  } catch {
    return undefined;
  }
}

export function updateEntity(
  ventureId: string,
  entityId: string,
  updates: Partial<Omit<GraphEntity, 'id' | 'ventureId' | 'createdAt'>>,
): GraphEntity | undefined {
  const existing = getEntity(ventureId, entityId);
  if (!existing) return undefined;

  const updated: GraphEntity = {
    ...existing,
    ...updates,
    id: existing.id,
    ventureId: existing.ventureId,
    createdAt: existing.createdAt,
    updatedAt: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
  };

  writeFileSync(entityPath(ventureId, entityId), JSON.stringify(updated, null, 2), 'utf-8');
  return updated;
}

export function removeEntity(ventureId: string, entityId: string): boolean {
  const path = entityPath(ventureId, entityId);
  if (!existsSync(path)) return false;

  // Move to .deleted/ (soft-delete pattern — recoverable)
  const trashDir = join(ENTITIES_DIR(ventureId), '.deleted');
  if (!existsSync(trashDir)) mkdirSync(trashDir, { recursive: true });
  const trashPath = join(trashDir, `${entityId}.json`);
  renameSync(path, trashPath);
  return true;
}

// ─── Relationship CRUD ───────────────────────────────────────────────────────

export function addRelationship(
  ventureId: string,
  rel: Omit<GraphRelationship, 'id' | 'createdAt'>,
): GraphRelationship {
  ensureGraphDir(ventureId);
  const now = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');

  const fullRel: GraphRelationship = {
    ...rel,
    id: generateId('rel', ventureId),
    createdAt: now,
  };

  const relsPath = relationshipPath(ventureId);
  writeFileSync(relsPath, JSON.stringify(fullRel) + '\n', { flag: 'a' });
  return fullRel;
}

export function getRelationships(ventureId: string): GraphRelationship[] {
  const relsPath = relationshipPath(ventureId);
  if (!existsSync(relsPath)) return [];

  const relationships: GraphRelationship[] = [];
  for (const line of readFileSync(relsPath, 'utf-8').split('\n').filter((l) => l.trim())) {
    try {
      relationships.push(JSON.parse(line) as GraphRelationship);
    } catch { /* skip malformed */ }
  }
  return relationships;
}

// ─── Query ───────────────────────────────────────────────────────────────────

export function queryEntities(ventureId: string, query: GraphQuery): GraphEntity[] {
  const dir = ENTITIES_DIR(ventureId);
  if (!existsSync(dir)) return [];

  const results: GraphEntity[] = [];
  let allEntities: GraphEntity[] = [];

  for (const file of readdirSync(dir)) {
    if (file.startsWith('.') || !file.endsWith('.json')) continue;
    const fullPath = join(dir, file);
    try {
      const entity = JSON.parse(readFileSync(fullPath, 'utf-8')) as GraphEntity;
      allEntities.push(entity);
    } catch { /* skip corrupt */ }
  }

  // Apply filters
  for (const e of allEntities) {
    if (query.type && e.type !== query.type) continue;
    if (query.label && !e.labels.includes(query.label)) continue;
    if (query.ventureId && e.ventureId !== query.ventureId && e.ventureId !== undefined) continue;
    results.push(e);
  }

  const limit = query.limit ?? results.length;
  return results.slice(0, limit);
}

export function queryRelationships(ventureId: string, query: GraphQuery): GraphRelationship[] {
  let allRels = getRelationships(ventureId);

  // Filter by venture if specified (or all if not)
  if (query.ventureId) {
    allRels = allRels.filter((r) => r.ventureId === query.ventureId);
  }

  // Filter by source/target
  if (query.sourceId) {
    allRels = allRels.filter((r) => r.sourceId === query.sourceId);
  }
  if (query.targetId) {
    allRels = allRels.filter((r) => r.targetId === query.targetId);
  }
  if (query.type) {
    allRels = allRels.filter((r) => r.type === query.type);
  }

  const limit = query.limit ?? allRels.length;
  return allRels.slice(0, limit);
}

export function query(ventureId: string, query: GraphQuery): GraphQueryResult {
  const entities = queryEntities(ventureId, query);
  const relationships = queryRelationships(ventureId, query);
  return {
    entities,
    relationships,
    totalFound: entities.length + relationships.length,
  };
}

// ─── Cross-Entity Traversal ──────────────────────────────────────────────────

/**
 * Find all paths from source entity through relationships up to maxDepth.
 * Returns entity ids in traversal order.
 */
export function tracePaths(ventureId: string, sourceId: string, maxDepth: number = 3): string[][] {
  const visited = new Set<string>([sourceId]);
  const paths: string[][] = [[sourceId]];

  const rels = getRelationships(ventureId);

  let depth = 0;
  while (depth < maxDepth && paths.length > 0) {
    const nextPaths: string[][] = [];
    for (const path of paths) {
      const current = path[path.length - 1];
      // Find all outgoing from current
      const outgoing = rels.filter(
        (r) => r.sourceId === current && !visited.has(r.targetId),
      );
      const incoming = rels.filter(
        (r) => r.targetId === current && !visited.has(r.sourceId),
      );

      const neighbors = [
        ...outgoing.map((r) => ({ id: r.targetId, direction: 'out' as const })),
        ...incoming.map((r) => ({ id: r.sourceId, direction: 'in' as const })),
      ];

      for (const n of neighbors) {
        visited.add(n.id);
        nextPaths.push([...path, n.id]);
      }
    }
    paths.length = 0;
    paths.push(...nextPaths);
    depth++;
  }

  return paths;
}

/**
 * Find entities related to a given entity id via any relationship path.
 */
export function getRelated(ventureId: string, entityId: string): { entity: GraphEntity; relType: string }[] {
  const rels = getRelationships(ventureId);
  const entityMap = new Map<string, GraphEntity>();

  const results: { entity: GraphEntity; relType: string }[] = [];

  for (const r of rels) {
    if (r.sourceId === entityId) {
      const target = getEntity(ventureId, r.targetId);
      if (target) results.push({ entity: target, relType: r.type });
    }
    if (r.targetId === entityId) {
      const source = getEntity(ventureId, r.sourceId);
      if (source) results.push({ entity: source, relType: r.type });
    }
  }

  return results;
}

// ─── Stats ───────────────────────────────────────────────────────────────────

export function getStats(ventureId: string): GraphStats {
  const dir = ENTITIES_DIR(ventureId);
  const entityTypes: Record<string, number> = {};
  let entityCount = 0;

  if (existsSync(dir)) {
    for (const file of readdirSync(dir)) {
      if (file.startsWith('.') || !file.endsWith('.json')) continue;
      try {
        const entity = JSON.parse(readFileSync(join(dir, file), 'utf-8')) as GraphEntity;
        entityTypes[entity.type] = (entityTypes[entity.type] || 0) + 1;
        entityCount++;
      } catch { /* skip */ }
    }
  }

  const rels = getRelationships(ventureId);
  const relTypes: Record<string, number> = {};
  for (const r of rels) {
    relTypes[r.type] = (relTypes[r.type] || 0) + 1;
  }

  return {
    entityCount,
    relationshipCount: rels.length,
    entityTypes,
    relationshipTypes: relTypes,
  };
}

// ─── Cross-Venture Queries ────────────────────────────────────────────────────

export function searchAllVentures(
  venturesRoot: string,
  query: { type?: string; label?: string; limit?: number },
): Array<GraphEntity & { ventureId: string }> {
  const results: Array<GraphEntity & { ventureId: string }> = [];
  const limit = query.limit ?? 50;

  if (!existsSync(venturesRoot)) return results;

  for (const vId of readdirSync(venturesRoot)) {
    const dir = join(venturesRoot, vId, 'knowledge', 'graph', 'entities');
    if (!existsSync(dir)) continue;

    for (const file of readdirSync(dir)) {
      if (file.startsWith('.') || !file.endsWith('.json')) continue;
      if (results.length >= limit) break;
      try {
        const entity = JSON.parse(readFileSync(join(dir, file), 'utf-8')) as GraphEntity;
        if (query.type && entity.type !== query.type) continue;
        if (query.label && !entity.labels.includes(query.label)) continue;
        results.push({ ...entity, ventureId: vId });
      } catch { /* skip */ }
    }
    if (results.length >= limit) break;
  }

  return results;
}
