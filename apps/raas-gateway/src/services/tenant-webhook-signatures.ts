/**
 * Tenant Webhook Signatures Service
 * Manage webhook signing keys and verification logs for tenants
 * Tables: webhook_signing_keys, webhook_signature_logs
 */

// ---- list signing keys ------------------------------------------------------

async function listKeys(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, key_name, algorithm, status, created_at, updated_at
         FROM webhook_signing_keys
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();
    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to list keys' };
  }
}

// ---- create signing key -----------------------------------------------------

interface CreateKeyInput {
  keyName: string;
  secret: string;
  algorithm?: string;
}

async function createKey(
  db: any,
  tenantId: string,
  input: CreateKeyInput
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const { keyName, secret, algorithm = 'hmac-sha256' } = input;

    if (!keyName || !secret) {
      return { success: false, error: 'keyName and secret are required' };
    }

    // Hash the secret before storage — never persist raw secret
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secret);
    const hashBuffer = await crypto.subtle.digest('SHA-256', keyData);
    const hashHex = Array.from(new Uint8Array(hashBuffer))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');

    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO webhook_signing_keys
           (id, tenant_id, key_name, secret_hash, algorithm, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 'active', ?, ?)`
      )
      .bind(id, tenantId, keyName, hashHex, algorithm, now, now)
      .run();

    return {
      success: true,
      data: { id, tenantId, keyName, algorithm, status: 'active', createdAt: now },
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to create key' };
  }
}

// ---- get signature logs -----------------------------------------------------

async function getLogs(
  db: any,
  tenantId: string,
  limit = 50
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 200);
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, signing_key_id, webhook_url, verified, created_at
         FROM webhook_signature_logs
         WHERE tenant_id = ?
         ORDER BY created_at DESC
         LIMIT ?`
      )
      .bind(tenantId, safeLimit)
      .all();
    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to fetch logs' };
  }
}

// ---- admin overview ---------------------------------------------------------

async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const [keysRow, logsRow, verifiedRow] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as total FROM webhook_signing_keys`).first(),
      db.prepare(`SELECT COUNT(*) as total FROM webhook_signature_logs`).first(),
      db
        .prepare(`SELECT COUNT(*) as total FROM webhook_signature_logs WHERE verified = 1`)
        .first(),
    ]);

    const totalLogs = (logsRow as any)?.total ?? 0;
    const totalVerified = (verifiedRow as any)?.total ?? 0;
    const verificationRate =
      totalLogs > 0 ? Math.round((totalVerified / totalLogs) * 100) : 0;

    return {
      success: true,
      data: {
        totalSigningKeys: (keysRow as any)?.total ?? 0,
        totalSignatureLogs: totalLogs,
        totalVerified,
        verificationRate,
        generatedAt: new Date().toISOString(),
      },
    };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : 'Failed to fetch overview',
    };
  }
}

// ---- exports ----------------------------------------------------------------

export const tenantWebhookSignaturesService = {
  listKeys,
  createKey,
  getLogs,
  getAdminOverview,
};
