/**
 * raas-onboarding.ts — Tenant onboarding: registration, API key generation, billing hook
 * Pure functions — wire to any HTTP framework or CLI.
 */
import { registerTenant, getTenant } from './raas-gateway.js';
import type { TenantLicense } from './raas-gateway.js';
import { TIER_CONFIGS } from './raas-pricing.js';
import type { RaasTier } from './raas-pricing.js';
import type { ApiResponse } from './raas-api.js';
import { randomBytes } from 'node:crypto';

// --- Types ---

export interface OnboardingRequest {
  tenantId: string;
  tier: RaasTier;
  email: string;
  companyName?: string;
}

export interface OnboardingResult {
  tenantId: string;
  apiKey: string;
  tier: RaasTier;
  expiresAt: number;
  creditsPerMonth: number;
}

export interface ApiKeyRecord {
  apiKey: string;
  tenantId: string;
  createdAt: number;
  active: boolean;
}

// --- In-memory API key store (production would use DB/KV) ---

const apiKeys = new Map<string, ApiKeyRecord>();
const tenantKeys = new Map<string, string[]>(); // tenantId → apiKey[]

// --- Core Functions ---

/** Generate a cryptographically random API key */
export function generateApiKey(prefix = 'mk'): string {
  const bytes = randomBytes(24);
  return `${prefix}_${bytes.toString('base64url')}`;
}

/** Full onboarding: validate → register tenant → generate API key */
export function handleOnboardTenant(req: OnboardingRequest): ApiResponse<OnboardingResult> {
  if (!req.tenantId || !req.email) {
    return { ok: false, status: 400, error: 'Missing tenantId or email' };
  }

  if (!(req.tier in TIER_CONFIGS)) {
    return { ok: false, status: 400, error: `Invalid tier: ${req.tier}` };
  }

  // Check if tenant already exists
  const existing = getTenant(req.tenantId);
  if (existing) {
    return { ok: false, status: 409, error: `Tenant "${req.tenantId}" already exists` };
  }

  const config = TIER_CONFIGS[req.tier];
  const expiresAt = Date.now() + 30 * 86_400_000; // 30 days

  // Register tenant license
  const license: TenantLicense = {
    tenantId: req.tenantId,
    tier: req.tier,
    active: true,
    expiresAt,
    usedCredits: 0,
  };
  registerTenant(license);

  // Generate API key
  const apiKey = generateApiKey();
  const keyRecord: ApiKeyRecord = {
    apiKey,
    tenantId: req.tenantId,
    createdAt: Date.now(),
    active: true,
  };
  apiKeys.set(apiKey, keyRecord);

  const existing_keys = tenantKeys.get(req.tenantId) ?? [];
  existing_keys.push(apiKey);
  tenantKeys.set(req.tenantId, existing_keys);

  return {
    ok: true,
    status: 201,
    data: {
      tenantId: req.tenantId,
      apiKey,
      tier: req.tier,
      expiresAt,
      creditsPerMonth: config.creditsPerMonth,
    },
  };
}

/** Validate an API key and return its tenant */
export function validateApiKey(apiKey: string): ApiResponse<{ tenantId: string; tier: RaasTier }> {
  const record = apiKeys.get(apiKey);
  if (!record) {
    return { ok: false, status: 401, error: 'Invalid API key' };
  }
  if (!record.active) {
    return { ok: false, status: 403, error: 'API key revoked' };
  }
  const tenant = getTenant(record.tenantId);
  if (!tenant) {
    return { ok: false, status: 404, error: 'Tenant not found' };
  }
  return { ok: true, status: 200, data: { tenantId: record.tenantId, tier: tenant.tier } };
}

/** Revoke an API key */
export function revokeApiKey(apiKey: string): ApiResponse<{ revoked: boolean }> {
  const record = apiKeys.get(apiKey);
  if (!record) {
    return { ok: false, status: 404, error: 'API key not found' };
  }
  record.active = false;
  return { ok: true, status: 200, data: { revoked: true } };
}

/** List all API keys for a tenant */
export function listTenantApiKeys(tenantId: string): ApiResponse<ApiKeyRecord[]> {
  const keys = tenantKeys.get(tenantId);
  if (!keys || keys.length === 0) {
    return { ok: true, status: 200, data: [] };
  }
  const records = keys.map(k => apiKeys.get(k)).filter(Boolean) as ApiKeyRecord[];
  return { ok: true, status: 200, data: records };
}
