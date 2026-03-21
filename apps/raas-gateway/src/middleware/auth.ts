/**
 * Authentication middleware — validates JWT or API key
 */

import type { MiddlewareHandler } from 'hono';
import { AuthService } from '../services/auth-service';
import { CreditService } from '../services/credit-service';
import type { Env } from '../index';
import type { TenantContext } from '../types/auth';
import { AuthenticationError } from '../utils/errors';
import { json } from '../utils/response';

// Extend Hono context with tenant info
declare module 'hono' {
  interface ContextVariableMap {
    tenant: TenantContext;
    authService: AuthService;
  }
}

/**
 * Authentication middleware factory
 * Returns middleware that validates JWT or API key
 */
export function auth(): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const authService = new AuthService(c.env);

    // Try JWT first
    const authHeader = c.req.header('Authorization');
    if (authHeader?.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const result = await authService.validateJwt(token);

      if (result.authenticated && result.tenant) {
        c.set('tenant', result.tenant);
        c.set('authService', authService);
        await next();
        await addCreditHeaders(c);
        return;
      }
    }

    // Try API key
    const apiKey = c.req.header('X-API-Key');
    if (apiKey) {
      const result = await authService.validateApiKey(apiKey);

      if (result.authenticated && result.tenant) {
        c.set('tenant', result.tenant);
        c.set('authService', authService);
        await next();
        await addCreditHeaders(c);
        return;
      }
    }

    // No valid auth found - return 401
    return json(
      { error: 'Valid JWT or API key required', code: 'AUTHENTICATION_REQUIRED' },
      { status: 401 }
    );
  };
}

/**
 * Get tenant from context (call after auth middleware)
 */
export function getTenant(c: { get: (key: string) => any }): TenantContext {
  const tenant = c.get('tenant');
  if (!tenant) {
    throw new Error('Tenant not found in context — ensure auth middleware ran');
  }
  return tenant;
}

/**
 * Get auth service from context
 */
export function getAuthService(c: { get: (key: string) => any }): AuthService {
  return c.get('authService');
}

/**
 * Add credit balance + warning headers to response
 */
async function addCreditHeaders(c: any): Promise<void> {
  try {
    const tenant = c.get('tenant');
    if (!tenant?.tenantId || !c.env?.DB) return;

    const creditService = new CreditService(c.env);
    const balance = await creditService.getBalance(tenant.tenantId);

    c.header('X-Credits-Remaining', balance.toString());
    if (balance === 0) {
      c.header('X-Credits-Warning', 'low');
      c.header('X-Credits-Alert', 'exhausted');
    } else if (balance < 5) {
      c.header('X-Credits-Warning', 'low');
      c.header('X-Credits-Alert', 'low');
    }
  } catch {
    // Non-critical — don't break the response
  }
}
