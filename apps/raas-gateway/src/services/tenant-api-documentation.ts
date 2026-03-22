/**
 * Tenant API Documentation Service
 * List pages, create pages, get version history, and admin overview
 */

// List documentation pages for a tenant with optional pagination
async function listPages(
  db: any,
  tenantId: string,
  limit = 50,
  offset = 0
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 200);
    const rows = await db
      .prepare(
        `SELECT id, page_title, slug, category, published, created_at, updated_at
         FROM api_documentation_pages
         WHERE tenant_id = ?
         ORDER BY created_at DESC
         LIMIT ? OFFSET ?`
      )
      .bind(tenantId, safeLimit, offset)
      .all();

    const countRow = await db
      .prepare('SELECT COUNT(*) as total FROM api_documentation_pages WHERE tenant_id = ?')
      .bind(tenantId)
      .first();

    return {
      success: true,
      data: {
        pages: rows.results ?? [],
        total: countRow?.total ?? 0,
        limit: safeLimit,
        offset,
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create a new documentation page for a tenant
async function createPage(
  db: any,
  tenantId: string,
  page: {
    pageTitle: string;
    slug: string;
    content?: string;
    category?: string;
    published?: boolean;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO api_documentation_pages
           (id, tenant_id, page_title, slug, content, category, published)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        page.pageTitle,
        page.slug,
        page.content ?? null,
        page.category ?? 'guide',
        page.published ? 1 : 0
      )
      .run();

    return { success: true, data: { id } };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Get version history for a specific documentation page
async function getVersions(
  db: any,
  tenantId: string,
  pageId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, version, edited_by, created_at
         FROM api_documentation_versions
         WHERE page_id = ? AND tenant_id = ?
         ORDER BY version DESC
         LIMIT 50`
      )
      .bind(pageId, tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Admin overview — aggregate documentation stats across all tenants
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totals, topTenants, recentPages] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total_pages,
             COUNT(DISTINCT tenant_id) as active_tenants,
             SUM(CASE WHEN published = 1 THEN 1 ELSE 0 END) as published_pages,
             SUM(CASE WHEN published = 0 THEN 1 ELSE 0 END) as draft_pages
           FROM api_documentation_pages`
        )
        .first(),

      db
        .prepare(
          `SELECT tenant_id, COUNT(*) as page_count
           FROM api_documentation_pages
           GROUP BY tenant_id
           ORDER BY page_count DESC
           LIMIT 10`
        )
        .all(),

      db
        .prepare(
          `SELECT id, tenant_id, page_title, category, published, created_at
           FROM api_documentation_pages
           ORDER BY created_at DESC
           LIMIT 20`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        totals,
        topTenants: topTenants.results ?? [],
        recentPages: recentPages.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const tenantApiDocumentationService = {
  listPages,
  createPage,
  getVersions,
  getAdminOverview,
};
