/**
 * Marketplace Payment Service — revenue share for template sellers
 * Commission split: 70% seller / 30% platform (configurable per seller)
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface MarketplaceSeller {
  id: string;
  tenant_id: string;
  display_name: string;
  payout_email: string | null;
  commission_rate: number;
  total_earnings: number;
  total_payouts: number;
  status: 'active' | 'suspended' | 'pending_review';
  created_at: string;
  updated_at: string;
}

export interface MarketplaceTransaction {
  id: string;
  seller_id: string;
  buyer_tenant_id: string;
  template_id: string;
  amount: number;
  seller_share: number;
  platform_share: number;
  currency: string;
  status: 'pending' | 'completed' | 'refunded';
  created_at: string;
}

export interface MarketplacePayout {
  id: string;
  seller_id: string;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  payout_method: string;
  reference: string | null;
  created_at: string;
  completed_at: string | null;
}

// ── Service functions ──────────────────────────────────────────────────────────

/** Register tenant as marketplace seller — idempotent */
export async function registerSeller(
  db: D1Database,
  tenantId: string,
  input: { display_name: string; payout_email?: string }
): Promise<MarketplaceSeller> {
  const existing = await db.prepare('SELECT * FROM marketplace_sellers WHERE tenant_id = ?')
    .bind(tenantId).first<MarketplaceSeller>();
  if (existing) return existing;

  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO marketplace_sellers (id, tenant_id, display_name, payout_email, updated_at)
     VALUES (?, ?, ?, ?, datetime('now'))`
  ).bind(id, tenantId, input.display_name, input.payout_email ?? null).run();

  return db.prepare('SELECT * FROM marketplace_sellers WHERE id = ?')
    .bind(id).first<MarketplaceSeller>() as Promise<MarketplaceSeller>;
}

/** Get seller profile by tenant ID */
export async function getSellerProfile(db: D1Database, tenantId: string): Promise<MarketplaceSeller | null> {
  return db.prepare('SELECT * FROM marketplace_sellers WHERE tenant_id = ?')
    .bind(tenantId).first<MarketplaceSeller>();
}

/** Update seller display name or payout email */
export async function updateSellerProfile(
  db: D1Database,
  tenantId: string,
  input: { display_name?: string; payout_email?: string }
): Promise<MarketplaceSeller | null> {
  const seller = await getSellerProfile(db, tenantId);
  if (!seller) return null;

  const display_name = input.display_name ?? seller.display_name;
  const payout_email = input.payout_email ?? seller.payout_email;

  await db.prepare(
    `UPDATE marketplace_sellers SET display_name = ?, payout_email = ?, updated_at = datetime('now') WHERE tenant_id = ?`
  ).bind(display_name, payout_email, tenantId).run();

  return getSellerProfile(db, tenantId);
}

/** Record a template purchase and split revenue between seller and platform */
export async function recordPurchase(
  db: D1Database,
  sellerId: string,
  buyerTenantId: string,
  templateId: string,
  amount: number,
  commissionRate: number
): Promise<MarketplaceTransaction> {
  const sellerShare = Math.round(amount * commissionRate * 100) / 100;
  const platformShare = Math.round((amount - sellerShare) * 100) / 100;
  const id = crypto.randomUUID();

  await db.batch([
    db.prepare(
      `INSERT INTO marketplace_transactions (id, seller_id, buyer_tenant_id, template_id, amount, seller_share, platform_share)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, sellerId, buyerTenantId, templateId, amount, sellerShare, platformShare),
    db.prepare(
      `UPDATE marketplace_sellers SET total_earnings = total_earnings + ?, updated_at = datetime('now') WHERE id = ?`
    ).bind(sellerShare, sellerId),
  ]);

  return db.prepare('SELECT * FROM marketplace_transactions WHERE id = ?')
    .bind(id).first<MarketplaceTransaction>() as Promise<MarketplaceTransaction>;
}

/** List transactions for a seller with optional pagination */
export async function getSellerTransactions(
  db: D1Database,
  sellerId: string,
  opts: { limit?: number; offset?: number } = {}
): Promise<MarketplaceTransaction[]> {
  const limit = opts.limit ?? 50;
  const offset = opts.offset ?? 0;
  const result = await db.prepare(
    'SELECT * FROM marketplace_transactions WHERE seller_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?'
  ).bind(sellerId, limit, offset).all<MarketplaceTransaction>();
  return result.results;
}

/** Aggregate earnings summary: total earned, paid out, available balance */
export async function getSellerEarnings(db: D1Database, sellerId: string): Promise<{
  total_earnings: number; total_payouts: number; available_balance: number;
} | null> {
  const seller = await db.prepare('SELECT total_earnings, total_payouts FROM marketplace_sellers WHERE id = ?')
    .bind(sellerId).first<Pick<MarketplaceSeller, 'total_earnings' | 'total_payouts'>>();
  if (!seller) return null;
  return {
    total_earnings: seller.total_earnings,
    total_payouts: seller.total_payouts,
    available_balance: Math.round((seller.total_earnings - seller.total_payouts) * 100) / 100,
  };
}

/** Create a payout request — validates sufficient balance */
export async function requestPayout(
  db: D1Database,
  sellerId: string,
  amount: number
): Promise<{ success: boolean; payout?: MarketplacePayout; error?: string }> {
  const earnings = await getSellerEarnings(db, sellerId);
  if (!earnings) return { success: false, error: 'Seller not found' };
  if (earnings.available_balance < amount) {
    return { success: false, error: `Insufficient balance. Available: ${earnings.available_balance}` };
  }

  const id = crypto.randomUUID();
  await db.batch([
    db.prepare(
      `INSERT INTO marketplace_payouts (id, seller_id, amount) VALUES (?, ?, ?)`
    ).bind(id, sellerId, amount),
    db.prepare(
      `UPDATE marketplace_sellers SET total_payouts = total_payouts + ?, updated_at = datetime('now') WHERE id = ?`
    ).bind(amount, sellerId),
  ]);

  const payout = await db.prepare('SELECT * FROM marketplace_payouts WHERE id = ?')
    .bind(id).first<MarketplacePayout>();
  return { success: true, payout: payout! };
}

/** List payout history for a seller */
export async function getPayouts(db: D1Database, sellerId: string): Promise<MarketplacePayout[]> {
  const result = await db.prepare(
    'SELECT * FROM marketplace_payouts WHERE seller_id = ? ORDER BY created_at DESC'
  ).bind(sellerId).all<MarketplacePayout>();
  return result.results;
}

/** Admin: mark pending payouts as processing */
export async function processPayouts(db: D1Database): Promise<{ processed: number }> {
  const result = await db.prepare(
    `UPDATE marketplace_payouts SET status = 'processing' WHERE status = 'pending'`
  ).run();
  return { processed: result.meta.changes ?? 0 };
}

/** Admin: platform-wide revenue and payout stats */
export async function getMarketplaceStats(db: D1Database): Promise<{
  total_sellers: number;
  total_revenue: number;
  total_seller_earnings: number;
  total_platform_revenue: number;
  total_payouts_completed: number;
  pending_payouts: number;
}> {
  const [sellers, revenue, payouts] = await Promise.all([
    db.prepare('SELECT COUNT(*) as count FROM marketplace_sellers WHERE status = ?').bind('active').first<{ count: number }>(),
    db.prepare('SELECT SUM(amount) as total, SUM(seller_share) as seller_total, SUM(platform_share) as platform_total FROM marketplace_transactions WHERE status = ?').bind('completed').first<{ total: number; seller_total: number; platform_total: number }>(),
    db.prepare("SELECT SUM(CASE WHEN status='completed' THEN amount ELSE 0 END) as completed, SUM(CASE WHEN status='pending' THEN amount ELSE 0 END) as pending FROM marketplace_payouts").first<{ completed: number; pending: number }>(),
  ]);

  return {
    total_sellers: sellers?.count ?? 0,
    total_revenue: revenue?.total ?? 0,
    total_seller_earnings: revenue?.seller_total ?? 0,
    total_platform_revenue: revenue?.platform_total ?? 0,
    total_payouts_completed: payouts?.completed ?? 0,
    pending_payouts: payouts?.pending ?? 0,
  };
}
