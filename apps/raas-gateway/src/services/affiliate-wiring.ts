/**
 * Affiliate Wiring Service — bridges affiliate engine into signup/payment flows
 */

import type { D1Database } from '@cloudflare/workers-types';
import { recordReferral, recordCommission } from './affiliate-service';

export interface CommissionResult {
  commission_id: string;
  partner_id: string;
  amount: number;
  currency: string;
  rate: number;
  transaction_id: string;
}

export interface PartnerEarnings {
  partner_id: string;
  total_earned: number;
  total_paid: number;
  pending: number;
  referral_count: number;
  conversion_rate: number;
}

export interface PayoutResult {
  payout_id: string;
  partner_id: string;
  amount: number;
  payout_method: string;
  status: 'pending';
}

export interface ReferralChain {
  tenant_id: string;
  partner_id: string;
  partner_code: string;
  referred_at: string;
  lifetime_value: number;
}

const DEFAULT_RATE = 0.20;

/** Process referral at signup — silently ignores invalid/missing codes */
export async function processSignupReferral(
  db: D1Database, tenantId: string, referralCode?: string
): Promise<{ id: string; partner_code: string } | null> {
  if (!referralCode) return null;
  try {
    const partner = await db.prepare(
      `SELECT id, partner_code FROM affiliate_partners WHERE partner_code = ? AND status = 'active'`
    ).bind(referralCode.toUpperCase()).first<{ id: string; partner_code: string }>();
    if (!partner) return null;

    const result = await recordReferral(db, referralCode.toUpperCase(), tenantId);
    if (!result.success) return null;

    await db.prepare(
      `INSERT OR IGNORE INTO tenant_referrals (id, tenant_id, partner_id, referral_code)
       VALUES (?, ?, ?, ?)`
    ).bind(crypto.randomUUID(), tenantId, partner.id, referralCode.toUpperCase()).run();

    return { id: partner.id, partner_code: partner.partner_code };
  } catch {
    return null; // non-blocking
  }
}

/** Process 20% commission when payment confirmed — null if no referral partner */
export async function processPaymentCommission(
  db: D1Database, tenantId: string, amount: number, currency: string, transactionId: string
): Promise<CommissionResult | null> {
  try {
    const referral = await db.prepare(
      `SELECT tr.partner_id, ap.commission_rate
       FROM tenant_referrals tr
       JOIN affiliate_partners ap ON ap.id = tr.partner_id
       WHERE tr.tenant_id = ? AND ap.status = 'active'`
    ).bind(tenantId).first<{ partner_id: string; commission_rate: number }>();
    if (!referral) return null;

    const rate = referral.commission_rate ?? DEFAULT_RATE;
    const commission = await recordCommission(db, referral.partner_id, tenantId, amount, rate);

    await db.prepare(
      `UPDATE tenant_referrals SET lifetime_value = lifetime_value + ?,
       first_payment_at = COALESCE(first_payment_at, datetime('now'))
       WHERE tenant_id = ?`
    ).bind(amount, tenantId).run();

    return {
      commission_id: commission.id,
      partner_id: referral.partner_id,
      amount: commission.commission_amount,
      currency,
      rate,
      transaction_id: transactionId,
    };
  } catch {
    return null;
  }
}

/** Total earned, pending, paid, conversion rate for a partner */
export async function getPartnerEarnings(db: D1Database, partnerId: string): Promise<PartnerEarnings | null> {
  try {
    const partner = await db.prepare(
      `SELECT total_earned, total_paid, total_referrals FROM affiliate_partners WHERE id = ?`
    ).bind(partnerId).first<{ total_earned: number; total_paid: number; total_referrals: number }>();
    if (!partner) return null;

    const paid = await db.prepare(
      `SELECT COUNT(*) as cnt FROM affiliate_commissions WHERE partner_id = ? AND status = 'paid'`
    ).bind(partnerId).first<{ cnt: number }>();

    const conversions = paid?.cnt ?? 0;
    return {
      partner_id: partnerId,
      total_earned: partner.total_earned,
      total_paid: partner.total_paid,
      pending: partner.total_earned - partner.total_paid,
      referral_count: partner.total_referrals,
      conversion_rate: partner.total_referrals > 0 ? conversions / partner.total_referrals : 0,
    };
  } catch {
    return null;
  }
}

/** Mark pending commissions as paid, record payout */
export async function processCommissionPayout(
  db: D1Database, partnerId: string, payoutMethod: string
): Promise<PayoutResult | null> {
  try {
    const row = await db.prepare(
      `SELECT SUM(commission_amount) as total FROM affiliate_commissions
       WHERE partner_id = ? AND status = 'approved'`
    ).bind(partnerId).first<{ total: number | null }>();

    const amount = row?.total ?? 0;
    if (amount <= 0) return null;

    const payoutId = crypto.randomUUID();
    await Promise.all([
      db.prepare(
        `UPDATE affiliate_commissions SET status = 'paid' WHERE partner_id = ? AND status = 'approved'`
      ).bind(partnerId).run(),
      db.prepare(
        `INSERT INTO affiliate_payouts (id, partner_id, amount, payout_method, status, processed_at)
         VALUES (?, ?, ?, ?, 'pending', datetime('now'))`
      ).bind(payoutId, partnerId, amount, payoutMethod).run(),
      db.prepare(
        `UPDATE affiliate_partners SET total_paid = total_paid + ?, updated_at = datetime('now') WHERE id = ?`
      ).bind(amount, partnerId).run(),
    ]);

    return { payout_id: payoutId, partner_id: partnerId, amount, payout_method: payoutMethod, status: 'pending' };
  } catch {
    return null;
  }
}

/** Referral chain — who referred this tenant and their stats */
export async function getReferralChain(db: D1Database, tenantId: string): Promise<ReferralChain | null> {
  try {
    const row = await db.prepare(
      `SELECT tr.partner_id, tr.referral_code, tr.signed_up_at, tr.lifetime_value, ap.partner_code
       FROM tenant_referrals tr
       JOIN affiliate_partners ap ON ap.id = tr.partner_id
       WHERE tr.tenant_id = ?`
    ).bind(tenantId).first<{
      partner_id: string; referral_code: string;
      signed_up_at: string; lifetime_value: number; partner_code: string;
    }>();
    if (!row) return null;
    return {
      tenant_id: tenantId,
      partner_id: row.partner_id,
      partner_code: row.partner_code,
      referred_at: row.signed_up_at,
      lifetime_value: row.lifetime_value,
    };
  } catch {
    return null;
  }
}
