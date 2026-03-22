/**
 * Tenant SSO Providers Service
 * Manages SSO provider configs, login flows, and sessions per tenant
 */

export const tenantSsoProvidersService = {
  /** List all SSO providers for a tenant */
  async listProviders(db: any, tenantId: string) {
    const { results } = await db
      .prepare('SELECT * FROM sso_providers WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return results;
  },

  /** Create a new SSO provider config */
  async createProvider(db: any, tenantId: string, data: Record<string, any>) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO sso_providers
         (id, tenant_id, provider_type, name, client_id, client_secret, metadata_url,
          issuer_url, callback_url, scopes_json, status, auto_provision, default_role, config_json, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id, tenantId,
        data.provider_type, data.name,
        data.client_id ?? null, data.client_secret ?? null,
        data.metadata_url ?? null, data.issuer_url ?? null,
        data.callback_url ?? null,
        data.scopes_json ?? '["openid","profile","email"]',
        data.status ?? 'active',
        data.auto_provision ?? 0,
        data.default_role ?? 'member',
        data.config_json ?? '{}',
        now, now
      )
      .run();
    return { id, tenant_id: tenantId, ...data, created_at: now, updated_at: now };
  },

  /** Get a single SSO provider by id, scoped to tenant */
  async getProvider(db: any, tenantId: string, id: string) {
    return db
      .prepare('SELECT * FROM sso_providers WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .first();
  },

  /** Update provider fields */
  async updateProvider(db: any, tenantId: string, id: string, data: Record<string, any>) {
    const now = new Date().toISOString();
    const fields = Object.keys(data)
      .filter(k => k !== 'id' && k !== 'tenant_id')
      .map(k => `${k} = ?`).join(', ');
    const values = Object.keys(data)
      .filter(k => k !== 'id' && k !== 'tenant_id')
      .map(k => data[k]);
    await db
      .prepare(`UPDATE sso_providers SET ${fields}, updated_at = ? WHERE id = ? AND tenant_id = ?`)
      .bind(...values, now, id, tenantId)
      .run();
    return this.getProvider(db, tenantId, id);
  },

  /** Delete a provider */
  async deleteProvider(db: any, tenantId: string, id: string) {
    const result = await db
      .prepare('DELETE FROM sso_providers WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .run();
    return { deleted: (result.meta?.changes ?? 0) > 0 };
  },

  /** Initiate SSO login — creates login attempt record */
  async initiateLogin(db: any, tenantId: string, providerId: string, ip: string, userAgent: string) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO sso_login_attempts (id, tenant_id, provider_id, status, ip_address, user_agent, created_at)
         VALUES (?, ?, ?, 'pending', ?, ?, ?)`
      )
      .bind(id, tenantId, providerId, ip, userAgent, now)
      .run();
    return { attempt_id: id, status: 'pending', created_at: now };
  },

  /** Complete SSO login — updates attempt and creates session */
  async completeLogin(db: any, tenantId: string, attemptId: string, userData: Record<string, any>) {
    const sessionId = crypto.randomUUID();
    const sessionToken = crypto.randomUUID();
    const now = new Date().toISOString();
    const expiresAt = new Date(Date.now() + 86400_000).toISOString(); // 24h

    const attempt = await db
      .prepare('SELECT * FROM sso_login_attempts WHERE id = ? AND tenant_id = ?')
      .bind(attemptId, tenantId)
      .first();
    if (!attempt) throw new Error('Login attempt not found');

    await db
      .prepare(`UPDATE sso_login_attempts SET status = 'completed' WHERE id = ?`)
      .bind(attemptId)
      .run();

    await db
      .prepare(
        `INSERT INTO sso_sessions (id, tenant_id, provider_id, user_email, external_id, session_token, expires_at, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(sessionId, tenantId, attempt.provider_id, userData.email, userData.external_id ?? null, sessionToken, expiresAt, now)
      .run();

    return { session_id: sessionId, session_token: sessionToken, expires_at: expiresAt };
  },

  /** List active sessions for a tenant */
  async listSessions(db: any, tenantId: string) {
    const { results } = await db
      .prepare('SELECT * FROM sso_sessions WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return results;
  },

  /** Revoke (delete) a session */
  async revokeSession(db: any, tenantId: string, sessionId: string) {
    const result = await db
      .prepare('DELETE FROM sso_sessions WHERE id = ? AND tenant_id = ?')
      .bind(sessionId, tenantId)
      .run();
    return { revoked: (result.meta?.changes ?? 0) > 0 };
  },

  /** Admin overview — counts across all tenants */
  async getAdminOverview(db: any) {
    const [providers, sessions, attempts] = await Promise.all([
      db.prepare('SELECT COUNT(*) as count, status FROM sso_providers GROUP BY status').all(),
      db.prepare('SELECT COUNT(*) as count FROM sso_sessions').first(),
      db.prepare("SELECT COUNT(*) as count, status FROM sso_login_attempts GROUP BY status").all(),
    ]);
    return {
      providers: providers.results,
      total_sessions: sessions?.count ?? 0,
      login_attempts: attempts.results,
    };
  },
};
