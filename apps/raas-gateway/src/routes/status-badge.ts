/**
 * Status badge SVG endpoints - embeddable badges
 */
import { Hono } from 'hono';
import type { Env } from '../index';

export const statusBadge = new Hono<{ Bindings: Env }>();

function svg(label: string, message: string, color: string): string {
  const lw = label.length * 7 + 10;
  const mw = message.length * 7 + 10;
  const w = lw + mw;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="20"><rect width="${lw}" height="20" fill="#555"/><rect x="${lw}" width="${mw}" height="20" fill="${color}"/><g fill="#fff" font-family="Verdana,sans-serif" font-size="11"><text x="${lw/2}" y="14" text-anchor="middle">${label}</text><text x="${lw + mw/2}" y="14" text-anchor="middle">${message}</text></g></svg>`;
}

/** GET /badge/status - system status SVG */
statusBadge.get('/badge/status', async (c) => {
  const cached = await c.env.RATE_LIMIT_KV.get('badge:status:svg');
  if (cached) return new Response(cached, { headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=60' } });
  let status = 'operational'; let color = '#4c1';
  try { await c.env.DB.prepare('SELECT 1').first(); } catch { status = 'degraded'; color = '#dfb317'; }
  const badge = svg('Mekong RaaS', status, color);
  await c.env.RATE_LIMIT_KV.put('badge:status:svg', badge, { expirationTtl: 60 });
  return new Response(badge, { headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=60' } });
});

/** GET /badge/status.json */
statusBadge.get('/badge/status.json', async (c) => {
  let status = 'operational'; let color = 'green';
  try { await c.env.DB.prepare('SELECT 1').first(); } catch { status = 'degraded'; color = 'yellow'; }
  return c.json({ schemaVersion: 1, label: 'Mekong RaaS', message: status, color });
});

/** GET /badge/version */
statusBadge.get('/badge/version', (c) => {
  return new Response(svg('API', 'v1.16.0', '#007ec6'), { headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=3600' } });
});

/** GET /badge/missions */
statusBadge.get('/badge/missions', async (c) => {
  const cached = await c.env.RATE_LIMIT_KV.get('badge:missions:svg');
  if (cached) return new Response(cached, { headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=300' } });
  const row = await c.env.DB.prepare("SELECT COUNT(*) as c FROM missions WHERE status='completed'").first<{c:number}>();
  const count = row?.c ?? 0;
  const badge = svg('missions', String(count), '#97ca00');
  await c.env.RATE_LIMIT_KV.put('badge:missions:svg', badge, { expirationTtl: 300 });
  return new Response(badge, { headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=300' } });
});
