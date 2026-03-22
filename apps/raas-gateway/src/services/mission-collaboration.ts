/**
 * Mission Collaboration Service — collaborators roster and threaded comments
 * Supports: listCollaborators, addCollaborator, getComments, getAdminOverview
 */

/**
 * List all collaborators for a mission scoped to a tenant
 */
async function listCollaborators(
  db: any,
  tenantId: string,
  missionId: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, mission_id, user_id, role, invited_by, joined_at
         FROM mission_collaborators
         WHERE tenant_id = ? AND mission_id = ?
         ORDER BY joined_at ASC`
      )
      .bind(tenantId, missionId)
      .all();
    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: 'Failed to list collaborators' };
  }
}

/**
 * Add a collaborator to a mission — generates a new UUID id
 */
async function addCollaborator(
  db: any,
  tenantId: string,
  missionId: string,
  userId: string,
  role: string = 'viewer',
  invitedBy?: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO mission_collaborators (id, tenant_id, mission_id, user_id, role, invited_by, joined_at)
         VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`
      )
      .bind(id, tenantId, missionId, userId, role, invitedBy ?? null)
      .run();

    const row = await db
      .prepare('SELECT * FROM mission_collaborators WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: row };
  } catch (err) {
    return { success: false, error: 'Failed to add collaborator' };
  }
}

/**
 * Get comments for a mission scoped to a tenant, optional parent_id filter for threading
 */
async function getComments(
  db: any,
  tenantId: string,
  missionId: string,
  parentId?: string | null
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = `SELECT id, tenant_id, mission_id, user_id, comment, parent_id, created_at
                 FROM mission_collaboration_comments
                 WHERE tenant_id = ? AND mission_id = ?`;
    const bindings: unknown[] = [tenantId, missionId];

    if (parentId !== undefined) {
      query += parentId === null ? ' AND parent_id IS NULL' : ' AND parent_id = ?';
      if (parentId !== null) bindings.push(parentId);
    }

    query += ' ORDER BY created_at ASC';

    const result = await db
      .prepare(query)
      .bind(...bindings)
      .all();

    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: 'Failed to get comments' };
  }
}

/**
 * Admin overview — collaborator counts grouped by tenant and comment totals
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const [collaboratorStats, commentStats] = await Promise.all([
      db
        .prepare(
          `SELECT tenant_id,
                  COUNT(*) as total_collaborators,
                  COUNT(DISTINCT mission_id) as missions_with_collaborators
           FROM mission_collaborators
           GROUP BY tenant_id
           ORDER BY total_collaborators DESC
           LIMIT 50`
        )
        .all(),
      db
        .prepare(
          `SELECT tenant_id,
                  COUNT(*) as total_comments,
                  COUNT(DISTINCT mission_id) as missions_with_comments
           FROM mission_collaboration_comments
           GROUP BY tenant_id
           ORDER BY total_comments DESC
           LIMIT 50`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        collaborators: collaboratorStats.results,
        comments: commentStats.results,
      },
    };
  } catch (err) {
    return { success: false, error: 'Failed to get admin overview' };
  }
}

export const missionCollaborationService = {
  listCollaborators,
  addCollaborator,
  getComments,
  getAdminOverview,
};
