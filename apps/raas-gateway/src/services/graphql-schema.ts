/**
 * GraphQL-like query executor — lightweight REST-to-GraphQL bridge
 * No external deps: runs on Cloudflare Workers with simple regex parsing
 */

export interface GraphQLRequest {
  query: string;
  variables?: Record<string, unknown>;
}

export interface GraphQLResponse {
  data?: Record<string, unknown>;
  errors?: Array<{ message: string; path?: string[] }>;
}

// ─── Argument parser ────────────────────────────────────────────────────────

/**
 * Parse inline arguments: `fieldName(key: "val", limit: 10)` → { key: "val", limit: 10 }
 */
function parseArgs(raw: string): Record<string, unknown> {
  const args: Record<string, unknown> = {};
  // Match key: "string" or key: number or key: true/false
  const pattern = /(\w+)\s*:\s*("([^"]*)"|([\d.]+)|(true|false))/g;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(raw)) !== null) {
    const key = m[1];
    if (m[3] !== undefined) args[key] = m[3];           // string
    else if (m[4] !== undefined) args[key] = parseFloat(m[4]); // number
    else if (m[5] !== undefined) args[key] = m[5] === 'true';  // boolean
  }
  return args;
}

// ─── Field selector ─────────────────────────────────────────────────────────

/**
 * Filter object/array to only include requested fields.
 * If fields is empty, return full object.
 */
function selectFields(data: unknown, fields: string[]): unknown {
  if (!fields.length || data === null || data === undefined) return data;
  if (Array.isArray(data)) return data.map((item) => selectFields(item, fields));
  if (typeof data === 'object') {
    const obj = data as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const f of fields) if (f in obj) out[f] = obj[f];
    return out;
  }
  return data;
}

// ─── Query parser ────────────────────────────────────────────────────────────

interface ParsedField {
  name: string;
  args: Record<string, unknown>;
  subFields: string[];
}

/**
 * Parse top-level fields from a GraphQL-like query string.
 * Supports: fieldName, fieldName(args), fieldName { subfields }
 */
function parseFields(body: string): ParsedField[] {
  const results: ParsedField[] = [];
  // Match: fieldName or fieldName(args) followed by optional { subfields }
  const topLevel = /(\w+)\s*(?:\(([^)]*)\))?\s*(?:\{([^}]*)\})?/g;
  let m: RegExpExecArray | null;
  while ((m = topLevel.exec(body)) !== null) {
    const name = m[1];
    // Skip GraphQL keywords
    if (['query', 'mutation', 'fragment', 'on'].includes(name)) continue;
    const args = m[2] ? parseArgs(m[2]) : {};
    const subFields = m[3]
      ? m[3].trim().split(/\s+/).filter(Boolean)
      : [];
    results.push({ name, args, subFields });
  }
  return results;
}

// ─── Resolvers ───────────────────────────────────────────────────────────────

const resolvers: Record<
  string,
  (args: Record<string, unknown>, db: D1Database, tenantId: string) => Promise<unknown>
> = {
  missions: async (args, db, tenantId) => {
    let sql = 'SELECT * FROM missions WHERE tenant_id = ?';
    const bindings: unknown[] = [tenantId];
    if (args.status) {
      sql += ' AND status = ?';
      bindings.push(args.status);
    }
    sql += ' ORDER BY created_at DESC';
    if (args.limit) {
      sql += ' LIMIT ?';
      bindings.push(Number(args.limit));
    }
    const r = await (db.prepare(sql).bind(...bindings) as D1PreparedStatement).all<Record<string, unknown>>();
    return r.results;
  },

  tenant: async (_args, db, tenantId) => {
    const r = await db
      .prepare('SELECT * FROM tenants WHERE id = ? LIMIT 1')
      .bind(tenantId)
      .first<Record<string, unknown>>();
    return r ?? null;
  },

  billing: async (_args, db, tenantId) => {
    const r = await db
      .prepare('SELECT credits_balance, tier, updated_at FROM tenants WHERE id = ? LIMIT 1')
      .bind(tenantId)
      .first<Record<string, unknown>>();
    return r ?? null;
  },

  analytics: async (_args, db, tenantId) => {
    const r = await db
      .prepare(
        `SELECT
          COUNT(*) AS total_missions,
          SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
          SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
          SUM(credits_cost) AS total_credits_used
         FROM missions WHERE tenant_id = ?`
      )
      .bind(tenantId)
      .first<Record<string, unknown>>();
    return r ?? {};
  },

  models: async (_args, _db, _tenantId) => {
    // Static registry — no DB query needed
    return [
      { id: 'auto', name: 'Auto-select', provider: 'openclaw' },
      { id: 'claude-sonnet', name: 'Claude Sonnet', provider: 'anthropic' },
      { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
      { id: 'qwen-plus', name: 'Qwen Plus', provider: 'dashscope' },
    ];
  },

  apiKeys: async (_args, db, tenantId) => {
    const r = await (db
      .prepare(
        'SELECT id, name, key_prefix, permissions, created_at, last_used_at FROM api_keys WHERE tenant_id = ? AND revoked = 0'
      )
      .bind(tenantId) as D1PreparedStatement).all<Record<string, unknown>>();
    return r.results;
  },
};

// ─── Mutations ───────────────────────────────────────────────────────────────

const mutations: Record<
  string,
  (args: Record<string, unknown>, db: D1Database, tenantId: string) => Promise<unknown>
> = {
  createMission: async (args, db, tenantId) => {
    const id = crypto.randomUUID();
    const goal = String(args.goal ?? '');
    const complexity = String(args.complexity ?? 'standard');
    const now = new Date().toISOString();
    await db
      .prepare(
        'INSERT INTO missions (id, tenant_id, goal, complexity, status, credits_cost, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
      )
      .bind(id, tenantId, goal, complexity, 'queued', 1, now)
      .run();
    return { id, tenantId, goal, complexity, status: 'queued', createdAt: now };
  },

  updateProfile: async (args, db, tenantId) => {
    const name = args.name ? String(args.name) : null;
    const email = args.email ? String(args.email) : null;
    if (!name && !email) throw new Error('Provide at least name or email');
    const setClauses: string[] = [];
    const bindings: unknown[] = [];
    if (name) { setClauses.push('name = ?'); bindings.push(name); }
    if (email) { setClauses.push('email = ?'); bindings.push(email); }
    bindings.push(tenantId);
    await db
      .prepare(`UPDATE tenants SET ${setClauses.join(', ')} WHERE id = ?`)
      .bind(...bindings)
      .run();
    return { updated: true };
  },
};

// ─── Main executor ───────────────────────────────────────────────────────────

/**
 * Execute a lightweight GraphQL-like query against D1.
 */
export async function executeGraphQL(
  request: GraphQLRequest,
  db: D1Database,
  tenantId: string
): Promise<GraphQLResponse> {
  const { query } = request;
  const trimmed = query.trim();
  const isMutation = trimmed.startsWith('mutation');

  // Strip outer wrapper: mutation { ... } or { ... }
  const braceOpen = trimmed.indexOf('{');
  const braceClose = trimmed.lastIndexOf('}');
  if (braceOpen === -1) {
    return { errors: [{ message: 'Invalid query: missing {' }] };
  }
  const body = trimmed.slice(braceOpen + 1, braceClose === -1 ? undefined : braceClose);

  const fields = parseFields(body);
  if (!fields.length) {
    return { errors: [{ message: 'No fields requested' }] };
  }

  const data: Record<string, unknown> = {};
  const errors: Array<{ message: string; path?: string[] }> = [];
  const resolverMap = isMutation ? mutations : resolvers;

  for (const field of fields) {
    const resolver = resolverMap[field.name];
    if (!resolver) {
      errors.push({ message: `Unknown field: ${field.name}`, path: [field.name] });
      continue;
    }
    try {
      const raw = await resolver(field.args, db, tenantId);
      data[field.name] = selectFields(raw, field.subFields);
    } catch (err) {
      errors.push({
        message: err instanceof Error ? err.message : 'Resolver error',
        path: [field.name],
      });
    }
  }

  return {
    ...(Object.keys(data).length ? { data } : {}),
    ...(errors.length ? { errors } : {}),
  };
}
