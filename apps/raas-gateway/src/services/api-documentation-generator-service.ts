/**
 * API Documentation Generator Service
 * CRUD for endpoints, versions, examples + OpenAPI spec generation
 */

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function newId(): string { return crypto.randomUUID(); }
function now(): string { return new Date().toISOString(); }

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

async function listEndpoints(db: any, filters?: { tag?: string; version?: string; deprecated?: string }) {
  let q = 'SELECT * FROM api_doc_endpoints';
  const params: any[] = [];
  const where: string[] = [];
  if (filters?.tag) { where.push('tag = ?'); params.push(filters.tag); }
  if (filters?.version) { where.push('version = ?'); params.push(filters.version); }
  if (filters?.deprecated !== undefined) { where.push('deprecated = ?'); params.push(filters.deprecated === 'true' ? 1 : 0); }
  if (where.length) q += ` WHERE ${where.join(' AND ')}`;
  q += ' ORDER BY tag, path, method';
  const { results } = await db.prepare(q).bind(...params).all();
  return results;
}

async function createEndpoint(db: any, data: any) {
  if (!data.path || !data.method) throw new Error('path and method are required');
  const id = newId();
  const ts = now();
  await db.prepare(
    `INSERT INTO api_doc_endpoints
     (id, path, method, summary, description, tag, request_schema_json, response_schema_json,
      example_request_json, example_response_json, auth_required, deprecated, version, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  ).bind(
    id, data.path, data.method.toUpperCase(),
    data.summary ?? null, data.description ?? null,
    data.tag ?? 'General',
    data.request_schema_json ?? '{}', data.response_schema_json ?? '{}',
    data.example_request_json ?? '{}', data.example_response_json ?? '{}',
    data.auth_required !== false ? 1 : 0,
    data.deprecated ? 1 : 0,
    data.version ?? 'v1', ts, ts,
  ).run();
  return { id, ...data, created_at: ts, updated_at: ts };
}

async function getEndpoint(db: any, id: string) {
  return db.prepare('SELECT * FROM api_doc_endpoints WHERE id = ?').bind(id).first();
}

async function updateEndpoint(db: any, id: string, data: any) {
  const allowed = ['path','method','summary','description','tag','request_schema_json',
    'response_schema_json','example_request_json','example_response_json','auth_required','deprecated','version'];
  const sets: string[] = []; const params: any[] = [];
  for (const [k, v] of Object.entries(data)) {
    if (allowed.includes(k)) { sets.push(`${k} = ?`); params.push(v); }
  }
  if (!sets.length) throw new Error('No valid fields to update');
  sets.push('updated_at = ?'); params.push(now()); params.push(id);
  await db.prepare(`UPDATE api_doc_endpoints SET ${sets.join(', ')} WHERE id = ?`).bind(...params).run();
  return getEndpoint(db, id);
}

async function deleteEndpoint(db: any, id: string) {
  await db.prepare('DELETE FROM api_doc_endpoints WHERE id = ?').bind(id).run();
}

// ---------------------------------------------------------------------------
// Versions
// ---------------------------------------------------------------------------

async function listVersions(db: any) {
  const { results } = await db.prepare('SELECT * FROM api_doc_versions ORDER BY created_at DESC').all();
  return results;
}

async function createVersion(db: any, data: any) {
  if (!data.version || !data.title) throw new Error('version and title are required');
  const id = newId();
  const ts = now();
  await db.prepare(
    'INSERT INTO api_doc_versions (id, version, title, description, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
  ).bind(id, data.version, data.title, data.description ?? null, data.status ?? 'draft', ts).run();
  return { id, ...data, status: data.status ?? 'draft', created_at: ts };
}

async function publishVersion(db: any, versionId: string) {
  const ts = now();
  await db.prepare(
    "UPDATE api_doc_versions SET status = 'published', published_at = ? WHERE id = ?",
  ).bind(ts, versionId).run();
  return db.prepare('SELECT * FROM api_doc_versions WHERE id = ?').bind(versionId).first();
}

// ---------------------------------------------------------------------------
// Examples
// ---------------------------------------------------------------------------

async function getExamples(db: any, endpointId: string) {
  const { results } = await db.prepare(
    'SELECT * FROM api_doc_examples WHERE endpoint_id = ? ORDER BY sort_order, created_at',
  ).bind(endpointId).all();
  return results;
}

async function addExample(db: any, endpointId: string, data: any) {
  if (!data.code) throw new Error('code is required');
  const id = newId();
  const ts = now();
  await db.prepare(
    'INSERT INTO api_doc_examples (id, endpoint_id, language, code, description, sort_order, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
  ).bind(id, endpointId, data.language ?? 'curl', data.code, data.description ?? null, data.sort_order ?? 0, ts).run();
  return { id, endpoint_id: endpointId, ...data, created_at: ts };
}

// ---------------------------------------------------------------------------
// Spec generation (OpenAPI 3.0 subset)
// ---------------------------------------------------------------------------

async function generateSpec(db: any, version: string) {
  const docVersion = await db.prepare('SELECT * FROM api_doc_versions WHERE version = ?').bind(version).first();
  const { results: endpoints } = await db.prepare(
    'SELECT * FROM api_doc_endpoints WHERE version = ? ORDER BY tag, path',
  ).bind(version).all();

  const paths: Record<string, any> = {};
  for (const ep of (endpoints as any[])) {
    if (!paths[ep.path]) paths[ep.path] = {};
    const method = ep.method.toLowerCase();
    paths[ep.path][method] = {
      summary: ep.summary, description: ep.description,
      tags: [ep.tag], deprecated: ep.deprecated === 1,
      security: ep.auth_required === 1 ? [{ ApiKeyAuth: [] }] : [],
      requestBody: ep.method !== 'GET' ? { content: { 'application/json': { schema: JSON.parse(ep.request_schema_json || '{}') } } } : undefined,
      responses: { '200': { description: 'Success', content: { 'application/json': { schema: JSON.parse(ep.response_schema_json || '{}') } } } },
    };
  }

  return {
    openapi: '3.0.0',
    info: { title: docVersion?.title ?? `API ${version}`, description: docVersion?.description ?? '', version },
    components: { securitySchemes: { ApiKeyAuth: { type: 'apiKey', in: 'header', name: 'X-API-Key' } } },
    paths,
  };
}

// ---------------------------------------------------------------------------
// Admin overview
// ---------------------------------------------------------------------------

async function getAdminOverview(db: any) {
  const [endpoints, versions, examples] = await Promise.all([
    db.prepare('SELECT COUNT(*) AS total, SUM(deprecated) AS deprecated_count FROM api_doc_endpoints').first(),
    db.prepare("SELECT COUNT(*) AS total, SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) AS published FROM api_doc_versions").first(),
    db.prepare('SELECT COUNT(*) AS total FROM api_doc_examples').first(),
  ]);
  const { results: byTag } = await db.prepare(
    'SELECT tag, COUNT(*) AS count FROM api_doc_endpoints GROUP BY tag ORDER BY count DESC',
  ).all();
  return { endpoints, versions, examples, by_tag: byTag };
}

// ---------------------------------------------------------------------------
// Exported service object
// ---------------------------------------------------------------------------

export const apiDocGeneratorService = {
  listEndpoints, createEndpoint, getEndpoint, updateEndpoint, deleteEndpoint,
  listVersions, createVersion, publishVersion,
  getExamples, addExample,
  generateSpec, getAdminOverview,
};
