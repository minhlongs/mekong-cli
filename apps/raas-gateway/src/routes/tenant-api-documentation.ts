/**
 * Tenant API Documentation routes
 * Mount at: /v1/api-documentation
 *
 * GET  /pages           — list doc pages (auth required)
 * POST /pages           — create doc page (auth required)
 * GET  /versions        — list page versions (auth required, ?page_id=)
 * GET  /admin/overview  — platform-wide stats (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiDocumentationService } from '../services/tenant-api-documentation';

type Bindings = {
  DB: any;
  ADMIN_KEY?: string;
  [key: string]: any;
};

const app = new Hono<{ Bindings: Bindings }>();

/** GET /pages — list documentation pages for authenticated tenant */
app.get('/pages', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
    const offset = parseInt(c.req.query('offset') ?? '0', 10) || 0;
    const result = await tenantApiDocumentationService.listPages(c.env.DB, tenant.tenantId, limit, offset);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** POST /pages — create a new documentation page for authenticated tenant */
app.post('/pages', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json();
    const pageTitle = (body.page_title ?? body.title ?? '').trim();
    const slug = (body.slug ?? '').trim();
    if (!pageTitle) return c.json({ error: 'page_title is required' }, 400);
    if (!slug) return c.json({ error: 'slug is required' }, 400);
    const result = await tenantApiDocumentationService.createPage(c.env.DB, tenant.tenantId, {
      pageTitle,
      slug,
      content: body.content,
      category: body.category,
      published: body.published,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /versions — list version history for a doc page (requires ?page_id=) */
app.get('/versions', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const pageId = c.req.query('page_id') ?? '';
    if (!pageId) return c.json({ error: 'page_id query param is required' }, 400);
    const result = await tenantApiDocumentationService.getVersions(c.env.DB, tenant.tenantId, pageId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

/** GET /admin/overview — platform-wide stats, requires X-Admin-Key header */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }
    const result = await tenantApiDocumentationService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

export { app as tenantApiDocumentation };
