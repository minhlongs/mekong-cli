/**
 * Changelog routes - public changelog + admin CRUD
 */
import { Hono } from 'hono';
import type { Env } from '../index';

export const changelog = new Hono<{ Bindings: Env }>();

function isAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

/** GET /changelog - list entries */
changelog.get('/changelog', async (c) => {
  const limit = Math.min(parseInt(c.req.query('limit') ?? '20', 10), 100);
  const category = c.req.query('category');
  let query = 'SELECT * FROM changelog_entries';
  const params: any[] = [];
  if (category) { query += ' WHERE category = ?'; params.push(category); }
  query += ' ORDER BY published_at DESC LIMIT ?';
  params.push(limit);
  const { results } = await c.env.DB.prepare(query).bind(...params).all();
  return c.json({ success: true, data: results });
});

/** GET /changelog/latest */
changelog.get('/changelog/latest', async (c) => {
  const entry = await c.env.DB.prepare('SELECT * FROM changelog_entries ORDER BY published_at DESC LIMIT 1').first();
  return c.json({ success: true, data: entry });
});

/** GET /changelog/rss - RSS feed */
changelog.get('/changelog/rss', async (c) => {
  const { results } = await c.env.DB.prepare('SELECT * FROM changelog_entries ORDER BY published_at DESC LIMIT 20').all();
  const items = (results as any[]).map((e: any) => `<item><title>${e.title}</title><description>${e.description}</description><pubDate>${e.published_at}</pubDate><category>${e.category}</category></item>`).join('');
  const xml = `<?xml version="1.0"?><rss version="2.0"><channel><title>Mekong RaaS Changelog</title><link>https://raas-gateway.agencyos-openclaw.workers.dev/changelog</link>${items}</channel></rss>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
});

/** POST /changelog - create (admin) */
changelog.post('/changelog', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const body = await c.req.json();
  if (!body.title || !body.description || !body.version) return c.json({ error: 'title, description, version required' }, 400);
  await c.env.DB.prepare('INSERT INTO changelog_entries (version, title, description, category, is_breaking) VALUES (?, ?, ?, ?, ?)').bind(body.version, body.title, body.description, body.category || 'feature', body.is_breaking ? 1 : 0).run();
  return c.json({ success: true, message: 'Entry created' }, 201);
});

/** PUT /changelog/:id - update (admin) */
changelog.put('/changelog/:id', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const id = c.req.param('id');
  const body = await c.req.json();
  const sets: string[] = []; const params: any[] = [];
  for (const [k, v] of Object.entries(body)) {
    if (['title', 'description', 'version', 'category', 'is_breaking'].includes(k)) { sets.push(`${k} = ?`); params.push(v); }
  }
  if (!sets.length) return c.json({ error: 'No valid fields' }, 400);
  params.push(id);
  await c.env.DB.prepare(`UPDATE changelog_entries SET ${sets.join(', ')} WHERE id = ?`).bind(...params).run();
  return c.json({ success: true });
});

/** DELETE /changelog/:id - delete (admin) */
changelog.delete('/changelog/:id', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  await c.env.DB.prepare('DELETE FROM changelog_entries WHERE id = ?').bind(c.req.param('id')).run();
  return c.json({ success: true });
});
