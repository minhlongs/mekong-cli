/**
 * Tenant Webhook Signatures Service
 * CRUD for webhook HMAC signatures + verification logs, and admin overview
 */

export interface WebhookSignature {
  id: string;
  tenant_id: string;
  algorithm: string;
  secret_key: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface SignatureVerification {
  id: string;
  tenant_id: string;
  signature_id: string;
  webhook_url: string;
  status: string;
  verified_at: string;
}

export interface CreateSignatureData {
  algorithm?: string;
  secret_key: string;
  is_active?: number;
}

/** List all webhook signatures for a tenant */
export async function listSignatures(db: any, tenantId: string): Promise<WebhookSignature[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM webhook_signatures WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return result.results as WebhookSignature[];
  } catch (err) {
    throw new Error(`listSignatures failed: ${String(err)}`);
  }
}

/** Create a new webhook signature for a tenant */
export async function createSignature(
  db: any,
  tenantId: string,
  data: CreateSignatureData
): Promise<WebhookSignature> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const algorithm = data.algorithm ?? 'sha256';
    const isActive = data.is_active ?? 1;

    await db
      .prepare(
        `INSERT INTO webhook_signatures (id, tenant_id, algorithm, secret_key, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, algorithm, data.secret_key, isActive, now, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM webhook_signatures WHERE id = ?')
      .bind(id)
      .first();
    return row as WebhookSignature;
  } catch (err) {
    throw new Error(`createSignature failed: ${String(err)}`);
  }
}

/** List signature verification logs for a tenant */
export async function getVerifications(db: any, tenantId: string): Promise<SignatureVerification[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM signature_verifications WHERE tenant_id = ? ORDER BY verified_at DESC')
      .bind(tenantId)
      .all();
    return result.results as SignatureVerification[];
  } catch (err) {
    throw new Error(`getVerifications failed: ${String(err)}`);
  }
}

/** Admin: platform-wide overview of webhook signatures */
export async function getAdminOverview(db: any): Promise<{
  total_signatures: number;
  active_signatures: number;
  total_verifications: number;
  by_algorithm: Record<string, number>;
  by_status: Record<string, number>;
  recent_verifications: SignatureVerification[];
}> {
  try {
    const [totalRow, activeRow, verifTotalRow, algorithmRows, statusRows, recentResult] =
      await Promise.all([
        db.prepare('SELECT COUNT(*) as total FROM webhook_signatures').first(),
        db.prepare('SELECT COUNT(*) as total FROM webhook_signatures WHERE is_active = 1').first(),
        db.prepare('SELECT COUNT(*) as total FROM signature_verifications').first(),
        db
          .prepare('SELECT algorithm, COUNT(*) as count FROM webhook_signatures GROUP BY algorithm')
          .all(),
        db
          .prepare('SELECT status, COUNT(*) as count FROM signature_verifications GROUP BY status')
          .all(),
        db
          .prepare('SELECT * FROM signature_verifications ORDER BY verified_at DESC LIMIT 10')
          .all(),
      ]);

    const by_algorithm: Record<string, number> = {};
    for (const row of algorithmRows.results as { algorithm: string; count: number }[]) {
      by_algorithm[row.algorithm] = row.count;
    }

    const by_status: Record<string, number> = {};
    for (const row of statusRows.results as { status: string; count: number }[]) {
      by_status[row.status] = row.count;
    }

    return {
      total_signatures: (totalRow as { total: number } | null)?.total ?? 0,
      active_signatures: (activeRow as { total: number } | null)?.total ?? 0,
      total_verifications: (verifTotalRow as { total: number } | null)?.total ?? 0,
      by_algorithm,
      by_status,
      recent_verifications: recentResult.results as SignatureVerification[],
    };
  } catch (err) {
    throw new Error(`getAdminOverview failed: ${String(err)}`);
  }
}

export const tenantWebhookSignaturesService = {
  listSignatures,
  createSignature,
  getVerifications,
  getAdminOverview,
};
