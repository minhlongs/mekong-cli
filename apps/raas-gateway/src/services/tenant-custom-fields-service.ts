/**
 * Tenant Custom Fields Service
 * CRUD for field definitions and values, bulk ops, search, admin overview
 */

const genId = () => crypto.randomUUID();
const now = () => new Date().toISOString();

// --- Definitions ---

async function listDefinitions(db: any, tenantId: string, entityType?: string): Promise<any[]> {
  const sql = entityType
    ? 'SELECT * FROM custom_field_definitions WHERE tenant_id = ? AND entity_type = ? ORDER BY sort_order ASC'
    : 'SELECT * FROM custom_field_definitions WHERE tenant_id = ? ORDER BY entity_type, sort_order ASC';
  const stmt = entityType
    ? db.prepare(sql).bind(tenantId, entityType)
    : db.prepare(sql).bind(tenantId);
  const { results } = await stmt.all();
  return results ?? [];
}

async function createDefinition(db: any, tenantId: string, data: any): Promise<any> {
  const id = genId();
  const ts = now();
  await db.prepare(`
    INSERT INTO custom_field_definitions
      (id, tenant_id, entity_type, field_name, field_type, label, description,
       required, default_value, validation_json, sort_order, searchable, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id, tenantId,
    data.entity_type, data.field_name,
    data.field_type ?? 'text', data.label,
    data.description ?? null,
    data.required ? 1 : 0,
    data.default_value ?? null,
    data.validation_json ? JSON.stringify(data.validation_json) : '{}',
    data.sort_order ?? 0,
    data.searchable !== false ? 1 : 0,
    ts, ts,
  ).run();
  return db.prepare('SELECT * FROM custom_field_definitions WHERE id = ?').bind(id).first();
}

async function getDefinition(db: any, tenantId: string, id: string): Promise<any> {
  return db.prepare(
    'SELECT * FROM custom_field_definitions WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).first();
}

async function updateDefinition(db: any, tenantId: string, id: string, data: any): Promise<any> {
  const ts = now();
  const fields: string[] = [];
  const values: any[] = [];

  const updatable = ['field_name', 'field_type', 'label', 'description', 'required',
    'default_value', 'sort_order', 'searchable'];
  for (const key of updatable) {
    if (key in data) {
      fields.push(`${key} = ?`);
      values.push(key === 'required' || key === 'searchable' ? (data[key] ? 1 : 0) : data[key]);
    }
  }
  if ('validation_json' in data) {
    fields.push('validation_json = ?');
    values.push(JSON.stringify(data.validation_json));
  }
  if (!fields.length) return getDefinition(db, tenantId, id);

  fields.push('updated_at = ?');
  values.push(ts, id, tenantId);
  await db.prepare(
    `UPDATE custom_field_definitions SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`
  ).bind(...values).run();
  return getDefinition(db, tenantId, id);
}

async function deleteDefinition(db: any, tenantId: string, id: string): Promise<boolean> {
  await db.prepare(
    'DELETE FROM custom_field_values WHERE definition_id = ? AND tenant_id = ?'
  ).bind(id, tenantId).run();
  const result = await db.prepare(
    'DELETE FROM custom_field_definitions WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).run();
  return (result.meta?.changes ?? 0) > 0;
}

// --- Values ---

async function getValues(db: any, tenantId: string, entityId: string): Promise<any[]> {
  const { results } = await db.prepare(`
    SELECT v.*, d.field_name, d.field_type, d.label
    FROM custom_field_values v
    JOIN custom_field_definitions d ON d.id = v.definition_id
    WHERE v.entity_id = ? AND v.tenant_id = ?
  `).bind(entityId, tenantId).all();
  return results ?? [];
}

async function setValue(db: any, tenantId: string, entityId: string, definitionId: string, value: any): Promise<any> {
  const existing = await db.prepare(
    'SELECT id FROM custom_field_values WHERE definition_id = ? AND entity_id = ?'
  ).bind(definitionId, entityId).first();
  const ts = now();
  const strVal = value !== null && value !== undefined ? String(value) : null;

  if (existing) {
    await db.prepare(
      'UPDATE custom_field_values SET value = ?, updated_at = ? WHERE definition_id = ? AND entity_id = ?'
    ).bind(strVal, ts, definitionId, entityId).run();
  } else {
    await db.prepare(
      'INSERT INTO custom_field_values (id, definition_id, entity_id, tenant_id, value, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(genId(), definitionId, entityId, tenantId, strVal, ts, ts).run();
  }
  return db.prepare(
    'SELECT * FROM custom_field_values WHERE definition_id = ? AND entity_id = ?'
  ).bind(definitionId, entityId).first();
}

async function bulkSetValues(db: any, tenantId: string, entityId: string, values: Record<string, any>): Promise<any[]> {
  const results = await Promise.all(
    Object.entries(values).map(([defId, val]) => setValue(db, tenantId, entityId, defId, val))
  );
  return results;
}

async function searchByField(db: any, tenantId: string, definitionId: string, value: string): Promise<any[]> {
  const { results } = await db.prepare(`
    SELECT v.entity_id, v.value, v.updated_at
    FROM custom_field_values v
    WHERE v.tenant_id = ? AND v.definition_id = ? AND v.value LIKE ?
  `).bind(tenantId, definitionId, `%${value}%`).all();
  return results ?? [];
}

// --- Admin ---

async function getAdminOverview(db: any): Promise<any> {
  const defs = await db.prepare(
    'SELECT COUNT(*) as total, COUNT(DISTINCT tenant_id) as tenants FROM custom_field_definitions'
  ).first();
  const vals = await db.prepare(
    'SELECT COUNT(*) as total FROM custom_field_values'
  ).first();
  const byType = await db.prepare(
    'SELECT entity_type, COUNT(*) as count FROM custom_field_definitions GROUP BY entity_type ORDER BY count DESC'
  ).all();
  return {
    definitions: { total: defs?.total ?? 0, tenants: defs?.tenants ?? 0 },
    values: { total: vals?.total ?? 0 },
    by_entity_type: byType.results ?? [],
  };
}

export const tenantCustomFieldsService = {
  listDefinitions,
  createDefinition,
  getDefinition,
  updateDefinition,
  deleteDefinition,
  getValues,
  setValue,
  bulkSetValues,
  searchByField,
  getAdminOverview,
};
