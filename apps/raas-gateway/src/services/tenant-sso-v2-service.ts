/** Tenant SSO V2 Service — SAML/OIDC identity provider management */
import type { D1Database } from '@cloudflare/workers-types';

export interface SSOConfig {
  id: string; tenant_id: string; provider_type: 'oidc' | 'saml'; provider_name: string;
  client_id?: string; client_secret_hash?: string; issuer_url?: string; metadata_url?: string;
  saml_certificate?: string; entity_id?: string; acs_url?: string; slo_url?: string;
  attribute_mapping: string; is_active: number; enforce_sso: number; allowed_domains: string;
  created_at: string; updated_at: string;
}
export interface SSOSession {
  id: string; tenant_id: string; sso_config_id: string; user_email: string; external_id?: string;
  state: string; nonce?: string; status: 'pending' | 'authenticated' | 'failed' | 'expired';
  identity_data: string; ip_address?: string; user_agent?: string; authenticated_at?: string;
  expires_at: string; created_at: string;
}

function generateToken(prefix = ''): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
  return prefix ? `${prefix}_${hex}` : hex;
}

/** Create a new SSO configuration for a tenant */
export async function createSSOConfig(db: D1Database, tenantId: string, config: Partial<SSOConfig>): Promise<SSOConfig> {
  const row = await db.prepare(
    `INSERT INTO sso_configurations
      (tenant_id,provider_type,provider_name,client_id,client_secret_hash,issuer_url,metadata_url,
       saml_certificate,entity_id,acs_url,slo_url,attribute_mapping,is_active,enforce_sso,allowed_domains)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING *`
  ).bind(
    tenantId, config.provider_type ?? 'oidc', config.provider_name,
    config.client_id ?? null, config.client_secret_hash ?? null,
    config.issuer_url ?? null, config.metadata_url ?? null, config.saml_certificate ?? null,
    config.entity_id ?? null, config.acs_url ?? null, config.slo_url ?? null,
    config.attribute_mapping ?? '{}', config.is_active ?? 1, config.enforce_sso ?? 0,
    config.allowed_domains ?? '[]'
  ).first<SSOConfig>();
  if (!row) throw new Error('Failed to create SSO configuration');
  return row;
}

/** List all SSO configurations for a tenant */
export async function listSSOConfigs(db: D1Database, tenantId: string): Promise<SSOConfig[]> {
  const r = await db.prepare('SELECT * FROM sso_configurations WHERE tenant_id = ? ORDER BY created_at DESC').bind(tenantId).all<SSOConfig>();
  return r.results;
}

/** Get a single SSO configuration scoped to tenant */
export async function getSSOConfig(db: D1Database, configId: string, tenantId: string): Promise<SSOConfig | null> {
  return db.prepare('SELECT * FROM sso_configurations WHERE id = ? AND tenant_id = ?').bind(configId, tenantId).first<SSOConfig>();
}

/** Update mutable fields of an SSO configuration */
export async function updateSSOConfig(db: D1Database, configId: string, tenantId: string, updates: Partial<SSOConfig>): Promise<SSOConfig | null> {
  const allowed = ['provider_name','client_id','client_secret_hash','issuer_url','metadata_url',
    'saml_certificate','entity_id','acs_url','slo_url','attribute_mapping','is_active','enforce_sso','allowed_domains'];
  const keys = Object.keys(updates).filter(k => allowed.includes(k));
  if (!keys.length) return getSSOConfig(db, configId, tenantId);
  const fields = keys.map(k => `${k} = ?`).join(', ');
  const values = keys.map(k => (updates as any)[k]);
  return db.prepare(
    `UPDATE sso_configurations SET ${fields}, updated_at = datetime('now') WHERE id = ? AND tenant_id = ? RETURNING *`
  ).bind(...values, configId, tenantId).first<SSOConfig>();
}

/** Soft-delete: deactivate an SSO configuration */
export async function deleteSSOConfig(db: D1Database, configId: string, tenantId: string): Promise<boolean> {
  const r = await db.prepare(
    `UPDATE sso_configurations SET is_active = 0, updated_at = datetime('now') WHERE id = ? AND tenant_id = ?`
  ).bind(configId, tenantId).run();
  return (r.meta?.changes ?? 0) > 0;
}

/** Initiate SSO login — generate CSRF state and return redirect URL */
export async function initiateSSOLogin(
  db: D1Database, tenantId: string, configId: string, opts?: { ip?: string; userAgent?: string }
): Promise<{ sessionId: string; state: string; redirectUrl: string }> {
  const config = await getSSOConfig(db, configId, tenantId);
  if (!config || !config.is_active) throw new Error('SSO configuration not found or inactive');
  const state = generateToken('st');
  const nonce = generateToken('nc');
  const expiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString();
  const session = await db.prepare(
    `INSERT INTO sso_sessions (tenant_id,sso_config_id,user_email,state,nonce,status,ip_address,user_agent,expires_at)
     VALUES (?,?,?,?,?,'pending',?,?,?) RETURNING id`
  ).bind(tenantId, configId, '', state, nonce, opts?.ip ?? null, opts?.userAgent ?? null, expiresAt).first<{ id: string }>();
  if (!session) throw new Error('Failed to create SSO session');
  const base = config.issuer_url ?? config.metadata_url ?? '';
  const redirectUrl = config.provider_type === 'oidc'
    ? `${base}/authorize?client_id=${config.client_id}&state=${state}&nonce=${nonce}&response_type=code&scope=openid+email+profile`
    : `${base}/sso/saml?SAMLRequest=&RelayState=${state}`;
  return { sessionId: session.id, state, redirectUrl };
}

/** Handle SSO callback — validate state, update session with identity claims */
export async function handleSSOCallback(db: D1Database, state: string, identityData: Record<string, unknown>): Promise<SSOSession> {
  const session = await db.prepare(`SELECT * FROM sso_sessions WHERE state = ? AND status = 'pending'`).bind(state).first<SSOSession>();
  if (!session) throw new Error('Invalid or expired SSO state');
  if (new Date(session.expires_at) < new Date()) {
    await db.prepare(`UPDATE sso_sessions SET status = 'expired' WHERE id = ?`).bind(session.id).run();
    throw new Error('SSO session expired');
  }
  const email = String(identityData.email ?? identityData.sub ?? '');
  const externalId = String(identityData.sub ?? identityData.nameId ?? '');
  const updated = await db.prepare(
    `UPDATE sso_sessions SET status = 'authenticated', user_email = ?, external_id = ?,
     identity_data = ?, authenticated_at = datetime('now') WHERE id = ? RETURNING *`
  ).bind(email, externalId, JSON.stringify(identityData), session.id).first<SSOSession>();
  if (!updated) throw new Error('Failed to update SSO session');
  return updated;
}

/** Get SSO session by ID */
export async function getSSOSession(db: D1Database, sessionId: string): Promise<SSOSession | null> {
  return db.prepare('SELECT * FROM sso_sessions WHERE id = ?').bind(sessionId).first<SSOSession>();
}

/** SSO authentication stats for a tenant */
export async function getSSOStats(db: D1Database, tenantId: string): Promise<{ total: number; authenticated: number; failed: number; pending: number }> {
  const row = await db.prepare(
    `SELECT COUNT(*) as total,
      SUM(CASE WHEN status='authenticated' THEN 1 ELSE 0 END) as authenticated,
      SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
      SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending
     FROM sso_sessions WHERE tenant_id = ?`
  ).bind(tenantId).first<{ total: number; authenticated: number; failed: number; pending: number }>();
  return row ?? { total: 0, authenticated: 0, failed: 0, pending: 0 };
}

/** Platform-wide SSO overview for admin */
export async function getAdminSSOOverview(db: D1Database): Promise<{ totalConfigs: number; activeConfigs: number; totalSessions: number; successRate: number }> {
  const [configs, sessions] = await Promise.all([
    db.prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM sso_configurations').first<{ total: number; active: number }>(),
    db.prepare(`SELECT COUNT(*) as total, SUM(CASE WHEN status='authenticated' THEN 1 ELSE 0 END) as authenticated FROM sso_sessions`).first<{ total: number; authenticated: number }>(),
  ]);
  const total = sessions?.total ?? 0;
  const authed = sessions?.authenticated ?? 0;
  return {
    totalConfigs: configs?.total ?? 0,
    activeConfigs: configs?.active ?? 0,
    totalSessions: total,
    successRate: total > 0 ? Math.round((authed / total) * 100) : 0,
  };
}
