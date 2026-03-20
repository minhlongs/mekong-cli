/**
 * Authentication service — handles JWT and API key validation
 */

import * as jose from 'jose';
import type { Env } from '../index';
import type { AuthResult, TenantContext, JwtPayload, ApiKeyRecord } from '../types/auth';

export class AuthService {
  constructor(private env: Env) {}

  /**
   * Validate JWT token
   */
  async validateJwt(token: string): Promise<AuthResult> {
    try {
      const secret = new TextEncoder().encode(this.env.JWT_SECRET=REDACTED);

      const { payload } = await jose.jwtVerify(token, secret, {
        issuer: 'raas-gateway',
        audience: 'raas-api',
      });

      const jwtPayload = payload as unknown as JwtPayload;

      // Check expiration
      if (jwtPayload.exp < Date.now() / 1000) {
        return { authenticated: false, error: 'Token expired' };
      }

      return {
        authenticated: true,
        tenant: {
          tenantId: jwtPayload.sub,
          tier: jwtPayload.tier as TenantContext['tier'],
          permissions: jwtPayload.permissions || [],
        },
      };
    } catch (error) {
      const err = error as Error & { code?: string };
      if (err.code === 'ERR_JWT_EXPIRED' || err.message.includes('expired')) {
        return { authenticated: false, error: 'Token expired' };
      }
      if (err.code === 'ERR_JWS_INVALID' || err.message.includes('invalid')) {
        return { authenticated: false, error: 'Invalid token' };
      }
      return { authenticated: false, error: 'Token validation failed' };
    }
  }

  /**
   * Validate API key
   */
  async validateApiKey(apiKey: string): Promise<AuthResult> {
    try {
      // Hash the provided key for comparison
      const encoder = new TextEncoder();
      const keyData = encoder.encode(apiKey);
      const hashBuffer = await crypto.subtle.digest('SHA-256', keyData);
      const keyHash = Array.from(new Uint8Array(hashBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');

      // Lookup in D1
      const result = await this.env.DB.prepare(
        `SELECT id, tenant_id, key_hash, name, revoked, permissions, last_used_at
         FROM api_keys
         WHERE key_hash = ? AND revoked = 0`
      )
        .bind(keyHash)
        .first<ApiKeyRecord>();

      if (!result) {
        return { authenticated: false, error: 'Invalid API key' };
      }

      // Get tenant info
      const tenant = await this.env.DB.prepare(
        'SELECT id, tier FROM tenants WHERE id = ? AND active = 1'
      )
        .bind(result.tenant_id)
        .first<{ id: string; tier: string }>();

      if (!tenant) {
        return { authenticated: false, error: 'Tenant not found or inactive' };
      }

      // Update last_used_at
      await this.env.DB.prepare(
        'UPDATE api_keys SET last_used_at = ? WHERE id = ?'
      )
        .bind(new Date().toISOString(), result.id)
        .run();

      return {
        authenticated: true,
        tenant: {
          tenantId: tenant.id,
          tier: tenant.tier as TenantContext['tier'],
          apiKeyId: result.id,
          permissions: result.permissions ? JSON.parse(result.permissions) : [],
        },
      };
    } catch (error) {
      console.error('[AuthService] API key validation error:', error);
      return { authenticated: false, error: 'Authentication failed' };
    }
  }

  /**
   * Generate JWT token for a tenant
   */
  async generateJwt(
    tenantId: string,
    tier: string,
    permissions: string[] = [],
    expiresIn = '24h'
  ): Promise<string> {
    const secret = new TextEncoder().encode(this.env.JWT_SECRET=REDACTED);

    const token = await new jose.SignJWT({
      sub: tenantId,
      tier,
      permissions,
    })
      .setProtectedHeader({ alg: 'HS256' })
      .setIssuedAt()
      .setIssuer('raas-gateway')
      .setAudience('raas-api')
      .setExpirationTime(expiresIn)
      .sign(secret);

    return token;
  }

  /**
   * Create new API key for tenant
   */
  async createApiKey(
    tenantId: string,
    name: string,
    permissions: string[] = []
  ): Promise<{ apiKey: string; keyId: string }> {
    // Generate random API key
    const bytes = new Uint8Array(24);
    crypto.getRandomValues(bytes);
    const apiKey = `mk_${Array.from(bytes)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')}`;

    // Hash the key
    const encoder = new TextEncoder();
    const keyData = encoder.encode(apiKey);
    const hashBuffer = await crypto.subtle.digest('SHA-256', keyData);
    const keyHash = Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    // Store in D1
    const keyId = crypto.randomUUID();
    await this.env.DB.prepare(
      `INSERT INTO api_keys (id, tenant_id, key_hash, name, permissions)
       VALUES (?, ?, ?, ?, ?)`
    )
      .bind(keyId, tenantId, keyHash, name, JSON.stringify(permissions))
      .run();

    return { apiKey, keyId };
  }

  /**
   * Revoke an API key
   */
  async revokeApiKey(keyId: string, tenantId: string): Promise<boolean> {
    const result = await this.env.DB.prepare(
      'UPDATE api_keys SET revoked = 1 WHERE id = ? AND tenant_id = ?'
    )
      .bind(keyId, tenantId)
      .run();

    return result.success && result.meta.changes > 0;
  }

  /**
   * Get all API keys for a tenant (without the hash)
   */
  async getApiKeys(tenantId: string): Promise<Omit<ApiKeyRecord, 'key_hash'>[]> {
    const results = await this.env.DB.prepare(
      'SELECT id, tenant_id, name, created_at, last_used_at, revoked, permissions FROM api_keys WHERE tenant_id = ?'
    )
      .bind(tenantId)
      .all<ApiKeyRecord>();

    return results.results.map(r => ({
      ...r,
      // key_hash is excluded
    }));
  }
}
