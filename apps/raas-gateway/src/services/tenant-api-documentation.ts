/**
 * Tenant API Documentation Service
 * Manage per-tenant documentation pages and version snapshots.
 */

export interface ApiDocPage {
  id: string;
  tenant_id: string;
  title: string;
  slug: string;
  content: string;
  category: string;
  sort_order: number;
  is_published: number;
  created_at: string;
  updated_at: string;
}

export interface ApiDocVersion {
  id: string;
  tenant_id: string;
  version_label: string;
  is_current: number;
  published_at: string | null;
  created_at: string;
}

export interface CreatePageData {
  title: string;
  slug: string;
  content?: string;
  category?: string;
  sort_order?: number;
  is_published?: number;
}

/** List all documentation pages for a tenant, ordered by sort_order then created_at */
export async function listPages(db: any, tenantId: string): Promise<ApiDocPage[]> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM api_doc_pages WHERE tenant_id = ? ORDER BY sort_order ASC, created_at ASC'
      )
      .bind(tenantId)
      .all();
    return (result.results ?? []) as ApiDocPage[];
  } catch (err) {
    throw new Error(`Failed to list doc pages: ${err}`);
  }
}

/** Create a new documentation page for a tenant */
export async function createPage(
  db: any,
  tenantId: string,
  data: CreatePageData
): Promise<ApiDocPage> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const content = data.content ?? '';
    const category = data.category ?? '';
    const sort_order = data.sort_order ?? 0;
    const is_published = data.is_published ?? 1;

    await db
      .prepare(
        `INSERT INTO api_doc_pages
           (id, tenant_id, title, slug, content, category, sort_order, is_published, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, data.title, data.slug, content, category, sort_order, is_published, now, now)
      .run();

    return {
      id,
      tenant_id: tenantId,
      title: data.title,
      slug: data.slug,
      content,
      category,
      sort_order,
      is_published,
      created_at: now,
      updated_at: now,
    };
  } catch (err) {
    throw new Error(`Failed to create doc page: ${err}`);
  }
}

/** List all doc versions for a tenant, ordered by created_at DESC */
export async function getVersions(db: any, tenantId: string): Promise<ApiDocVersion[]> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM api_doc_versions WHERE tenant_id = ? ORDER BY created_at DESC'
      )
      .bind(tenantId)
      .all();
    return (result.results ?? []) as ApiDocVersion[];
  } catch (err) {
    throw new Error(`Failed to get doc versions: ${err}`);
  }
}

/** Admin overview — page and version counts across all tenants */
export async function getAdminOverview(db: any): Promise<{
  total_pages: number;
  published_pages: number;
  total_versions: number;
  tenants_with_docs: number;
}> {
  try {
    const [pages, versions, tenants] = await Promise.all([
      db
        .prepare('SELECT COUNT(*) as total, SUM(is_published) as published FROM api_doc_pages')
        .first(),
      db.prepare('SELECT COUNT(*) as total FROM api_doc_versions').first(),
      db
        .prepare('SELECT COUNT(DISTINCT tenant_id) as total FROM api_doc_pages')
        .first(),
    ]);

    return {
      total_pages: Number(pages?.total ?? 0),
      published_pages: Number(pages?.published ?? 0),
      total_versions: Number(versions?.total ?? 0),
      tenants_with_docs: Number(tenants?.total ?? 0),
    };
  } catch (err) {
    throw new Error(`Failed to get admin overview: ${err}`);
  }
}

export const tenantApiDocumentationService = {
  listPages,
  createPage,
  getVersions,
  getAdminOverview,
};
