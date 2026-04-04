/**
 * credit-meter.ts — Credit metering for mekong-raas plugin.
 * Determines credit cost per command layer, checks balance, deducts atomically.
 *
 * Credit costs map to factory/layers.yaml layer ordering:
 *   studio=10, founder=8, business=5, product=3, engineering=2, ops=1
 */

import type { Tenant, CreditCheckResult, MekongLayer } from './types.js';
import { LAYER_CREDIT_COSTS } from './types.js';

/** In-memory credit ledger: tenantId → current balance.
 *  Production: replace with atomic Cloudflare KV / D1 transaction. */
const creditStore = new Map<string, number>();

/**
 * Determine command layer from a command string.
 * Checks for `layer:command` notation first, then falls back to keyword scan.
 * Returns null if the layer cannot be identified (treated as ops/cheapest).
 */
export function detectLayer(command: string): MekongLayer | null {
  if (!command) return null;

  // Support explicit layer prefix: "founder:raise", "engineering:cook"
  const colonIdx = command.indexOf(':');
  if (colonIdx > 0) {
    const prefix = command.slice(0, colonIdx).toLowerCase() as MekongLayer;
    if (prefix in LAYER_CREDIT_COSTS) return prefix;
  }

  // Keyword-based detection for unprefixed commands
  const cmd = command.toLowerCase();

  const LAYER_KEYWORDS: Record<MekongLayer, string[]> = {
    studio: ['studio', 'dealflow', 'portfolio', 'venture', 'expert', 'match-founder'],
    founder: ['annual', 'okr', 'fundraise', 'swot', 'raise', 'pitch', 'ipo', 'runway', 'moat'],
    business: ['sales', 'marketing', 'finance', 'hr', 'crm', 'invoice', 'campaign', 'sdr', 'ae'],
    product: ['plan', 'sprint', 'roadmap', 'brainstorm', 'scope', 'persona', 'design', 'ux'],
    engineering: ['cook', 'code', 'fix', 'test', 'deploy', 'review', 'refactor', 'debug', 'ship'],
    ops: ['audit', 'health', 'status', 'sync', 'clean', 'rollback', 'security', 'env'],
  };

  for (const [layer, keywords] of Object.entries(LAYER_KEYWORDS) as [MekongLayer, string[]][]) {
    if (keywords.some(kw => cmd.includes(kw))) return layer;
  }

  return null;
}

/**
 * Get credit cost for a command.
 * Falls back to ops cost (1) when layer is undetectable.
 */
export function getCreditCost(command: string, layerOverride?: MekongLayer | null): number {
  const layer = layerOverride ?? detectLayer(command) ?? 'ops';
  return LAYER_CREDIT_COSTS[layer];
}

/**
 * Initialize or load tenant credit balance into the in-memory store.
 * Call this when a tenant authenticates with their current DB balance.
 */
export function initTenantBalance(tenantId: string, balance: number): void {
  creditStore.set(tenantId, balance);
}

/**
 * Get current tenant credit balance from in-memory store.
 * Returns 0 if tenant is unknown.
 */
export function getBalance(tenantId: string): number {
  return creditStore.get(tenantId) ?? 0;
}

/**
 * Check if a tenant has sufficient credits and deduct atomically if so.
 *
 * Returns CreditCheckResult:
 *   - allowed=true: credits deducted, command may proceed
 *   - allowed=false + statusCode=402: insufficient credits
 *   - allowed=false + statusCode=404: tenant not found in store
 */
export function checkAndDeduct(
  tenant: Tenant,
  creditsRequired: number,
): CreditCheckResult {
  // Seed store from tenant object if not yet initialized
  if (!creditStore.has(tenant.tenantId)) {
    creditStore.set(tenant.tenantId, tenant.creditBalance);
  }

  const currentBalance = creditStore.get(tenant.tenantId);
  if (currentBalance === undefined) {
    return {
      allowed: false,
      statusCode: 404,
      reason: `Tenant "${tenant.tenantId}" not found in credit store`,
      creditsRequired,
      remainingAfter: 0,
    };
  }

  if (currentBalance < creditsRequired) {
    return {
      allowed: false,
      statusCode: 402,
      reason: `Insufficient credits: need ${creditsRequired}, have ${currentBalance}`,
      creditsRequired,
      remainingAfter: currentBalance,
    };
  }

  // Atomic deduction
  const newBalance = currentBalance - creditsRequired;
  creditStore.set(tenant.tenantId, newBalance);

  return {
    allowed: true,
    statusCode: 200,
    creditsRequired,
    remainingAfter: newBalance,
  };
}

/**
 * Refund credits to a tenant (used on command failure in after_dispatch).
 * No-op if tenant not in store.
 */
export function refundCredits(tenantId: string, amount: number): void {
  const current = creditStore.get(tenantId);
  if (current === undefined) return;
  creditStore.set(tenantId, current + amount);
}
