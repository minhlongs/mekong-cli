/**
 * Authentication type definitions
 */

export interface TenantContext {
  tenantId: string;
  tier: 'starter' | 'pro' | 'enterprise';
  apiKeyId?: string;
  permissions: string[];
}

export interface RateLimitTier {
  tier: 'starter' | 'pro' | 'enterprise';
  capacity: number;      // Max tokens (requests per minute)
  refillRate: number;    // Tokens added per second
}

export interface AuthResult {
  authenticated: boolean;
  tenant?: TenantContext;
  error?: string;
}

export interface JwtPayload {
  sub: string;        // tenant ID
  tier: string;
  permissions: string[];
  iat: number;
  exp: number;
  iss: string;
}

export interface ApiKeyRecord {
  id: string;
  tenant_id: string;
  key_hash: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
  revoked: boolean;
  permissions: string;  // JSON string from D1
}
