/**
 * IP Allowlist middleware — per-tenant IP filtering with KV cache
 * Empty allowlist = allow all (default open)
 * Has entries = allowlist mode (only matching IPs pass)
 * Enterprise tier: skip check entirely
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

const KV_TTL_SECONDS = 300; // 5 minutes

/** Get client IP from Cloudflare or forwarded headers */
function getClientIp(req: Request): string | null {
  return (
    req.headers.get('CF-Connecting-IP') ||
    req.headers.get('X-Forwarded-For')?.split(',')[0]?.trim() ||
    null
  );
}

/** Load tenant's allowlist IPs from KV cache or D1 */
async function getAllowlist(tenantId: string, env: Env): Promise<string[] | null> {
  const cacheKey = `iplist:${tenantId}`;

  // Try KV cache first
  const cached = await env.RATE_LIMIT_KV.get(cacheKey);
  if (cached !== null) {
    return JSON.parse(cached) as string[];
  }

  // Load from D1
  const rows = await env.DB.prepare(
    'SELECT cidr FROM ip_allowlist WHERE tenant_id = ?'
  ).bind(tenantId).all<{ cidr: string }>();

  const list = rows.results.map(r => r.cidr);

  // Cache result (empty list cached too — means no entries = allow all)
  await env.RATE_LIMIT_KV.put(cacheKey, JSON.stringify(list), {
    expirationTtl: KV_TTL_SECONDS,
  });

  return list;
}

/**
 * IP allowlist middleware factory.
 * Mount after auth middleware so tenant context is available.
 */
export function ipAllowlist(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const tenant = c.get('tenant');
    if (!tenant) return next(); // No tenant context — skip (auth handles 401)

    // Enterprise tier bypasses IP check
    if (tenant.tier === 'enterprise') return next();

    const allowlist = await getAllowlist(tenant.tenantId, c.env);

    // No entries = default open, allow all
    if (!allowlist || allowlist.length === 0) return next();

    const clientIp = getClientIp(c.req.raw);
    if (!clientIp || !allowlist.includes(clientIp)) {
      return json(
        { error: 'IP address not in tenant allowlist', code: 'IP_FORBIDDEN' },
        { status: 403 }
      );
    }

    return next();
  };
}
