/**
 * Admin Release Management Service
 * CRUD for platform_releases + platform_release_notes + dashboard aggregation
 */

// List all releases ordered by created_at desc, optional status filter
async function listReleases(
  db: any,
  status?: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = status
      ? await db
          .prepare(
            `SELECT * FROM platform_releases WHERE status = ?
             ORDER BY created_at DESC LIMIT 200`
          )
          .bind(status)
          .all()
      : await db
          .prepare(
            `SELECT * FROM platform_releases ORDER BY created_at DESC LIMIT 200`
          )
          .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create a new release record
async function createRelease(
  db: any,
  payload: {
    id: string;
    version: string;
    title: string;
    description?: string;
    release_type?: string;
    status?: string;
    released_at?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const {
      id,
      version,
      title,
      description,
      release_type = 'minor',
      status = 'draft',
      released_at,
    } = payload;
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO platform_releases
           (id, version, title, description, release_type, status, released_at, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        version,
        title,
        description ?? null,
        release_type,
        status,
        released_at ?? null,
        now,
        now
      )
      .run();

    const created = await db
      .prepare(`SELECT * FROM platform_releases WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// List release notes, optionally filtered by release_id or category
async function getNotes(
  db: any,
  releaseId?: string,
  category?: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    let query = `SELECT * FROM platform_release_notes`;
    const bindings: any[] = [];
    const conditions: string[] = [];

    if (releaseId) {
      conditions.push(`release_id = ?`);
      bindings.push(releaseId);
    }
    if (category) {
      conditions.push(`category = ?`);
      bindings.push(category);
    }
    if (conditions.length) {
      query += ` WHERE ` + conditions.join(' AND ');
    }
    query += ` ORDER BY created_at DESC LIMIT 500`;

    const stmt = db.prepare(query);
    const result = bindings.length ? await stmt.bind(...bindings).all() : await stmt.all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Dashboard: release counts by status + latest 5 releases + total notes
async function getDashboard(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [countRows, latestRows, noteCountRow] = await Promise.all([
      db
        .prepare(
          `SELECT status, COUNT(*) as count FROM platform_releases GROUP BY status`
        )
        .all(),
      db
        .prepare(
          `SELECT * FROM platform_releases ORDER BY created_at DESC LIMIT 5`
        )
        .all(),
      db
        .prepare(`SELECT COUNT(*) as total FROM platform_release_notes`)
        .first(),
    ]);

    const byStatus: Record<string, number> = {};
    for (const row of (countRows.results ?? []) as any[]) {
      byStatus[row.status] = row.count;
    }

    return {
      success: true,
      data: {
        byStatus,
        totalReleases: Object.values(byStatus).reduce(
          (a: number, b: any) => a + Number(b),
          0
        ),
        totalNotes: noteCountRow?.total ?? 0,
        latestReleases: latestRows.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminReleaseManagementService = {
  listReleases,
  createRelease,
  getNotes,
  getDashboard,
};
