/**
 * Affiliate Service — Partner registration, commission tracking, leaderboard
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AffiliatePartner {
  id: string;
  tenant_id: string;
  partner_code: string;
  commission_rate: number;
  status: 'active' | 'suspended' | 'terminated';
  total_referrals: number;
  total_earned: number;
  total_paid: number;
  payout_method: string;
  payout_details: string | null;
  created_at: string;
  updated_at: string;
}

export interface AffiliateCommission {
  id: string;
  partner_id: string;
  referred_tenant_id: string;
  payment_amount: number;
  commission_amount: number;
  status: 'pending' | 'approved' | 'paid' | 'rejected';
  period: string;
  created_at: string;
}

export interface AffiliateReferral {
  id: string;
  partner_id: string;
  referred_tenant_id: string;
  signup_at: string;
  first_payment_at: string | null;
  lifetime_value: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const genCode = (): string => Math.random().toString(36).slice(2, 10).toUpperCase();
const currentPeriod = (): string => new Date().toISOString().slice(0, 7);

// ── Service functions ──────────────────────────────────────────────────────────

/** Register tenant as affiliate — idempotent */
export async function registerPartner(db: D1Database, tenantId: string, payoutMethod = 'polar'): Promise<AffiliatePartner> {
  const existing = await db.prepare('SELECT * FROM affiliate_partners WHERE tenant_id = ?')
    .bind(tenantId).first<AffiliatePartner>();
  if (existing) return existing;

  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO affiliate_partners (id, tenant_id, partner_code, payout_method, updated_at)
     VALUES (?, ?, ?, ?, datetime('now'))`
  ).bind(id, tenantId, genCode(), payoutMethod).run();

  return db.prepare('SELECT * FROM affiliate_partners WHERE id = ?')
    .bind(id).first<AffiliatePartner>() as Promise<AffiliatePartner>;
}

/** Get partner stats for a tenant — null if not registered */
export async function getPartnerStats(db: D1Database, tenantId: string): Promise<AffiliatePartner | null> {
  return db.prepare('SELECT * FROM affiliate_partners WHERE tenant_id = ?')
    .bind(tenantId).first<AffiliatePartner>();
}

/** Link referred tenant to partner code at signup */
export async function recordReferral(
  db: D1Database, partnerCode: string, referredTenantId: string
): Promise<{ success: boolean; error?: string }> {
  const partner = await db.prepare(
    `SELECT id FROM affiliate_partners WHERE partner_code = ? AND status = 'active'`
  ).bind(partnerCode).first<{ id: string }>();
  if (!partner) return { success: false, error: 'Invalid or inactive partner code' };

  const dupe = await db.prepare('SELECT id FROM affiliate_referrals WHERE referred_tenant_id = ?')
    .bind(referredTenantId).first<{ id: string }>();
  if (dupe) return { success: false, error: 'Tenant already referred' };

  const id = crypto.randomUUID();
  await Promise.all([
    db.prepare('INSERT INTO affiliate_referrals (id, partner_id, referred_tenant_id) VALUES (?, ?, ?)')
      .bind(id, partner.id, referredTenantId).run(),
    db.prepare(`UPDATE affiliate_partners SET total_referrals = total_referrals + 1, updated_at = datetime('now') WHERE id = ?`)
      .bind(partner.id).run(),
  ]);
  return { success: true };
}

/** Record commission for a referred tenant's payment */
export async function recordCommission(
  db: D1Database, partnerId: string, referredTenantId: string,
  paymentAmount: number, commissionRate: number
): Promise<AffiliateCommission> {
  const commissionAmount = paymentAmount * commissionRate;
  const id = crypto.randomUUID();

  await Promise.all([
    db.prepare(
      `INSERT INTO affiliate_commissions (id, partner_id, referred_tenant_id, payment_amount, commission_amount, period)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(id, partnerId, referredTenantId, paymentAmount, commissionAmount, currentPeriod()).run(),
    db.prepare(`UPDATE affiliate_partners SET total_earned = total_earned + ?, updated_at = datetime('now') WHERE id = ?`)
      .bind(commissionAmount, partnerId).run(),
    db.prepare(
      `UPDATE affiliate_referrals SET lifetime_value = lifetime_value + ?,
       first_payment_at = COALESCE(first_payment_at, datetime('now'))
       WHERE partner_id = ? AND referred_tenant_id = ?`
    ).bind(paymentAmount, partnerId, referredTenantId).run(),
  ]);

  return db.prepare('SELECT * FROM affiliate_commissions WHERE id = ?')
    .bind(id).first<AffiliateCommission>() as Promise<AffiliateCommission>;
}

/** List commissions for a partner — optionally filtered by status */
export async function getCommissions(db: D1Database, partnerId: string, status?: string): Promise<AffiliateCommission[]> {
  const base = 'SELECT * FROM affiliate_commissions WHERE partner_id = ?';
  const result = status
    ? await db.prepare(`${base} AND status = ? ORDER BY created_at DESC`).bind(partnerId, status).all<AffiliateCommission>()
    : await db.prepare(`${base} ORDER BY created_at DESC`).bind(partnerId).all<AffiliateCommission>();
  return result.results ?? [];
}

/** Approve pending commissions by IDs */
export async function approveCommissions(db: D1Database, commissionIds: string[]): Promise<{ approved: number }> {
  if (!commissionIds.length) return { approved: 0 };
  const placeholders = commissionIds.map(() => '?').join(', ');
  const result = await db.prepare(
    `UPDATE affiliate_commissions SET status = 'approved' WHERE id IN (${placeholders}) AND status = 'pending'`
  ).bind(...commissionIds).run();
  return { approved: result.meta?.changes ?? 0 };
}

/** Top active affiliates ranked by total_earned */
export async function getLeaderboard(db: D1Database, limit = 10): Promise<AffiliatePartner[]> {
  const result = await db.prepare(
    `SELECT * FROM affiliate_partners WHERE status = 'active' ORDER BY total_earned DESC LIMIT ?`
  ).bind(limit).all<AffiliatePartner>();
  return result.results ?? [];
}

/** Admin — all partners regardless of status */
export async function adminGetAllPartners(db: D1Database): Promise<AffiliatePartner[]> {
  const result = await db.prepare('SELECT * FROM affiliate_partners ORDER BY created_at DESC')
    .all<AffiliatePartner>();
  return result.results ?? [];
}
