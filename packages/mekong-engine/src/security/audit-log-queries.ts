/**
 * Audit Log Database Operations & Row Mapping
 * Compatible with migration 0014 + 0015 schema
 */

export interface AuditLogEntry {
  id: string
  tenant_id?: string
  user_id?: string
  action: string
  resource?: string
  resource_id?: string
  resource_type?: string
  ip_address?: string
  user_agent?: string
  request_method?: string
  request_path?: string
  status_code?: number
  old_value?: string
  new_value?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface AuditLogFilters {
  tenant_id?: string
  action?: string
  resource?: string
  resource_type?: string
  resource_id?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

function mapAuditRow(row: Record<string, unknown>): AuditLogEntry {
  return {
    id: String(row.id),
    tenant_id: row.tenant_id ? String(row.tenant_id) : undefined,
    user_id: row.user_id ? String(row.user_id) : undefined,
    action: String(row.action),
    resource: row.resource ? String(row.resource) : undefined,
    resource_id: row.resource_id ? String(row.resource_id) : undefined,
    ip_address: row.ip_address ? String(row.ip_address) : undefined,
    user_agent: row.user_agent ? String(row.user_agent) : undefined,
    request_method: row.request_method ? String(row.request_method) : undefined,
    request_path: row.request_path ? String(row.request_path) : undefined,
    status_code: row.status_code ? Number(row.status_code) : undefined,
    old_value: row.old_value ? JSON.parse(row.old_value as string) : null,
    new_value: row.new_value ? JSON.parse(row.new_value as string) : null,
    metadata: row.metadata ? JSON.parse(row.metadata as string) : null,
    created_at: String(row.created_at),
  }
}

/**
 * Create audit log entry in D1 database
 */
export async function logAudit(
  db: D1Database,
  entry: Omit<AuditLogEntry, 'id' | 'created_at'>
): Promise<void> {
  try {
    const id = crypto.randomUUID()
    const created_at = new Date().toISOString()
    const metadata = entry.metadata ? JSON.stringify(entry.metadata) : null
    const old_value = entry.old_value ? JSON.stringify(entry.old_value) : null
    const new_value = entry.new_value ? JSON.stringify(entry.new_value) : null

    await db
      .prepare(`
        INSERT INTO audit_logs (
          id, tenant_id, user_id, action, resource, resource_id,
          ip_address, user_agent, request_method, request_path, status_code,
          old_value, new_value, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `)
      .bind(
        id,
        entry.tenant_id || null,
        entry.user_id || null,
        entry.action,
        entry.resource || entry.resource_type || null,
        entry.resource_id || null,
        entry.ip_address || null,
        entry.user_agent || null,
        entry.request_method || null,
        entry.request_path || null,
        entry.status_code || null,
        old_value,
        new_value,
        metadata,
        created_at
      )
      .run()
  } catch (error) {
    console.error('Audit log write failed:', error instanceof Error ? error.message : String(error))
  }
}

/**
 * Query audit logs with filters
 */
export async function queryAuditLogs(
  db: D1Database,
  filters: AuditLogFilters
): Promise<AuditLogEntry[]> {
  let sql = `
    SELECT id, tenant_id, user_id, action, resource, resource_id,
           ip_address, user_agent, request_method, request_path, status_code,
           old_value, new_value, metadata, created_at
    FROM audit_logs
    WHERE 1=1
  `
  const params: (string | number)[] = []

  if (filters.tenant_id) {
    sql += ' AND tenant_id = ?'
    params.push(filters.tenant_id)
  }
  if (filters.action) {
    sql += ' AND action = ?'
    params.push(filters.action)
  }
  if (filters.resource || filters.resource_type) {
    sql += ' AND resource = ?'
    params.push(filters.resource || filters.resource_type || '')
  }
  if (filters.resource_id) {
    sql += ' AND resource_id = ?'
    params.push(filters.resource_id)
  }
  if (filters.start_date) {
    sql += ' AND created_at >= ?'
    params.push(filters.start_date)
  }
  if (filters.end_date) {
    sql += ' AND created_at <= ?'
    params.push(filters.end_date)
  }

  sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
  params.push(filters.limit || 100, filters.offset || 0)

  const { results } = await db.prepare(sql).bind(...params).all()
  return (results as Record<string, unknown>[]).map((row: Record<string, unknown>) => mapAuditRow(row))
}

/**
 * Get single audit log by ID
 */
export async function getAuditLogById(
  db: D1Database,
  id: string
): Promise<AuditLogEntry | null> {
  const row = await db
    .prepare(`
      SELECT id, tenant_id, user_id, action, resource, resource_id,
             ip_address, user_agent, request_method, request_path, status_code,
             old_value, new_value, metadata, created_at
      FROM audit_logs
      WHERE id = ?
    `)
    .bind(id)
    .first()

  if (!row) return null
  return mapAuditRow(row as Record<string, unknown>)
}
