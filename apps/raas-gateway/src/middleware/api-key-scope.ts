/**
 * API key scope middleware — enforces read/write/admin permission hierarchy
 * Scope hierarchy: read < write < admin
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';
import { getTenant } from './auth';
import { json } from '../utils/response';

type Scope = 'read' | 'write' | 'admin';

const SCOPE_RANK: Record<Scope, number> = {
  read: 1,
  write: 2,
  admin: 3,
};

/**
 * Middleware factory — requires minimum scope on the API key used.
 * JWT auth always passes (full access).
 * API key auth must have scope >= minScope.
 */
export function requireScope(minScope: Scope): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const tenant = getTenant(c);

    // JWT auth: apiKeyId absent → full access, skip check
    if (!tenant.apiKeyId) {
      await next();
      return;
    }

    // API key auth: check scope stored in permissions array
    // Convention: permissions array contains 'scope:read', 'scope:write', or 'scope:admin'
    const scopeEntry = tenant.permissions.find((p) => p.startsWith('scope:'));
    const keyScope = (scopeEntry?.split(':')[1] ?? 'write') as Scope;
    const keyRank = SCOPE_RANK[keyScope] ?? SCOPE_RANK.write;
    const minRank = SCOPE_RANK[minScope];

    if (keyRank < minRank) {
      return json(
        {
          error: `API key scope '${keyScope}' insufficient — requires '${minScope}' or higher`,
          code: 'INSUFFICIENT_SCOPE',
        },
        { status: 403 }
      );
    }

    await next();
  };
}
