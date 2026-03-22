/**
 * Tenant Tag System Service — create/manage tags and entity associations
 * Supports tagging any entity type (mission, project, tenant, etc.)
 */

function newId(): string {
  return crypto.randomUUID();
}

/** List all tags for a tenant */
export async function listTags(db: any, tenantId: string): Promise<any[]> {
  const { results } = await db
    .prepare('SELECT * FROM tags WHERE tenant_id = ? ORDER BY name ASC')
    .bind(tenantId)
    .all();
  return results;
}

/** Create a new tag for a tenant */
export async function createTag(
  db: any,
  tenantId: string,
  data: { name: string; color?: string; description?: string }
): Promise<any> {
  const id = newId();
  await db
    .prepare(
      `INSERT INTO tags (id, tenant_id, name, color, description)
       VALUES (?, ?, ?, ?, ?)`
    )
    .bind(id, tenantId, data.name, data.color ?? '#6B7280', data.description ?? null)
    .run();
  return db.prepare('SELECT * FROM tags WHERE id = ?').bind(id).first();
}

/** Update an existing tag (name, color, description) */
export async function updateTag(
  db: any,
  tenantId: string,
  id: string,
  data: { name?: string; color?: string; description?: string }
): Promise<any> {
  const fields: string[] = [];
  const values: any[] = [];
  if (data.name !== undefined) { fields.push('name = ?'); values.push(data.name); }
  if (data.color !== undefined) { fields.push('color = ?'); values.push(data.color); }
  if (data.description !== undefined) { fields.push('description = ?'); values.push(data.description); }
  if (!fields.length) return db.prepare('SELECT * FROM tags WHERE id = ? AND tenant_id = ?').bind(id, tenantId).first();
  values.push(id, tenantId);
  await db.prepare(`UPDATE tags SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`).bind(...values).run();
  return db.prepare('SELECT * FROM tags WHERE id = ?').bind(id).first();
}

/** Delete a tag and all its entity associations */
export async function deleteTag(db: any, tenantId: string, id: string): Promise<void> {
  await db.prepare('DELETE FROM entity_tags WHERE tag_id = ? AND tenant_id = ?').bind(id, tenantId).run();
  await db.prepare('DELETE FROM tags WHERE id = ? AND tenant_id = ?').bind(id, tenantId).run();
}

/** Associate a tag with an entity; increments usage_count */
export async function tagEntity(
  db: any,
  tenantId: string,
  tagId: string,
  entityType: string,
  entityId: string
): Promise<any> {
  const id = newId();
  await db
    .prepare(
      `INSERT OR IGNORE INTO entity_tags (id, tenant_id, tag_id, entity_type, entity_id)
       VALUES (?, ?, ?, ?, ?)`
    )
    .bind(id, tenantId, tagId, entityType, entityId)
    .run();
  await db
    .prepare('UPDATE tags SET usage_count = usage_count + 1 WHERE id = ? AND tenant_id = ?')
    .bind(tagId, tenantId)
    .run();
  return db.prepare('SELECT * FROM entity_tags WHERE tag_id = ? AND entity_type = ? AND entity_id = ?')
    .bind(tagId, entityType, entityId).first();
}

/** Remove a tag from an entity; decrements usage_count */
export async function untagEntity(
  db: any,
  tenantId: string,
  tagId: string,
  entityType: string,
  entityId: string
): Promise<void> {
  const row = await db
    .prepare('SELECT id FROM entity_tags WHERE tag_id = ? AND entity_type = ? AND entity_id = ? AND tenant_id = ?')
    .bind(tagId, entityType, entityId, tenantId).first();
  if (!row) return;
  await db.prepare('DELETE FROM entity_tags WHERE tag_id = ? AND entity_type = ? AND entity_id = ? AND tenant_id = ?')
    .bind(tagId, entityType, entityId, tenantId).run();
  await db.prepare('UPDATE tags SET usage_count = MAX(0, usage_count - 1) WHERE id = ? AND tenant_id = ?')
    .bind(tagId, tenantId).run();
}

/** Get all tags for a specific entity */
export async function getEntityTags(
  db: any,
  tenantId: string,
  entityType: string,
  entityId: string
): Promise<any[]> {
  const { results } = await db
    .prepare(
      `SELECT t.* FROM tags t
       JOIN entity_tags et ON et.tag_id = t.id
       WHERE et.tenant_id = ? AND et.entity_type = ? AND et.entity_id = ?
       ORDER BY t.name ASC`
    )
    .bind(tenantId, entityType, entityId)
    .all();
  return results;
}

/** Find all entities tagged with a given tag, optionally filtered by entity_type */
export async function findByTag(
  db: any,
  tenantId: string,
  tagId: string,
  entityType?: string
): Promise<any[]> {
  const base = 'SELECT * FROM entity_tags WHERE tenant_id = ? AND tag_id = ?';
  const query = entityType ? `${base} AND entity_type = ?` : base;
  const bindings = entityType ? [tenantId, tagId, entityType] : [tenantId, tagId];
  const { results } = await db.prepare(query).bind(...bindings).all();
  return results;
}

/** Tag usage analytics for a tenant */
export async function getTagAnalytics(db: any, tenantId: string): Promise<any> {
  const { results: tags } = await db
    .prepare('SELECT * FROM tags WHERE tenant_id = ? ORDER BY usage_count DESC')
    .bind(tenantId).all();
  const { results: byType } = await db
    .prepare(
      `SELECT entity_type, COUNT(*) as count FROM entity_tags
       WHERE tenant_id = ? GROUP BY entity_type`
    )
    .bind(tenantId).all();
  return { tags, byEntityType: byType, totalTags: tags.length };
}

/** Admin overview across all tenants */
export async function getAdminOverview(db: any): Promise<any> {
  const { results: topTags } = await db
    .prepare('SELECT * FROM tags ORDER BY usage_count DESC LIMIT 20').all();
  const { results: tenantCounts } = await db
    .prepare('SELECT tenant_id, COUNT(*) as tag_count FROM tags GROUP BY tenant_id ORDER BY tag_count DESC LIMIT 20').all();
  const totalTagsRow = await db.prepare('SELECT COUNT(*) as total FROM tags').first();
  const totalAssocRow = await db.prepare('SELECT COUNT(*) as total FROM entity_tags').first();
  return {
    topTags,
    tenantCounts,
    totalTags: totalTagsRow?.total ?? 0,
    totalAssociations: totalAssocRow?.total ?? 0,
  };
}

export const tenantTagSystemService = {
  listTags,
  createTag,
  updateTag,
  deleteTag,
  tagEntity,
  untagEntity,
  getEntityTags,
  findByTag,
  getTagAnalytics,
  getAdminOverview,
};
