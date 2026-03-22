/**
 * Tenant API Documentation Routes
 * Per-tenant documentation page and version management.
 *
 * GET  /pages           — list doc pages (auth)
 * POST /pages           — create doc page (auth)
 * GET  /versions        — list doc versions (auth)
 * GET  /admin/overview  — admin stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiDocumentationService } from '../services/tenant-api-documentation';

const app = new Hono<{ Bindings: Env }>();

// GET /pages — list all documentation pages for authenticated tenant
app.get('/pages', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const pages = await tenantApiDocumentationService.listPages(c.env.DB, tenantId);
    return c.json({ pages, total: pages.length });
  } catch (err) {
    return c.json({ error: 'Failed to list doc pages' }, 500);
  }
});

// POST /pages — create a new documentation page
app.post('/pages', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      title?: string;
      slug?: string;
      content?: string;
      category?: string;
      sort_order?: number;
      is_published?: number;
    };

    const title = body.title?.trim();
    const slug = body.slug?.trim();

    if (!title) {
      return c.json({ error: 'title is required', code: 'VALIDATION_ERROR' }, 400);
    }
    if (!slug) {
      return c.json({ error: 'slug is required', code: 'VALIDATION_ERROR' }, 400);
    }

    const page = await tenantApiDocumentationService.createPage(c.env.DB, tenantId, {
      title,
      slug,
      content: body.content,
      category: body.category,
      sort_order: body.sort_order,
      is_published: body.is_published,
    });

    return c.json(page, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create doc page' }, 500);
  }
});

// GET /versions — list all doc versions for authenticated tenant
app.get('/versions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const versions = await tenantApiDocumentationService.getVersions(c.env.DB, tenantId);
    return c.json({ versions, total: versions.length });
  } catch (err) {
    return c.json({ error: 'Failed to list doc versions' }, 500);
  }
});

// GET /admin/overview — cross-tenant stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }

  try {
    const overview = await tenantApiDocumentationService.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (err) {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantApiDocumentation };
