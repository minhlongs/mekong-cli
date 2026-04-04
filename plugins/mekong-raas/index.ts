/**
 * plugins/mekong-raas/index.ts — Main RaaS plugin entry point.
 *
 * Registers with OpenClaw v2026.3.24+ hook system.
 * Two hooks:
 *   before_dispatch — authenticate tenant, validate credits, deduct, or block with 402
 *   after_dispatch  — log billing event, refund on failure
 *
 * Local use (no Authorization header) is always free — never metered.
 */

import { authenticateTenant } from './tenant-auth.js';
import {
  detectLayer,
  getCreditCost,
  initTenantBalance,
  checkAndDeduct,
  refundCredits,
  getBalance,
} from './credit-meter.js';
import { logBillingEvent } from './billing-logger.js';
import type {
  BeforeDispatchPayload,
  AfterDispatchPayload,
  HookResponse,
  DispatchContext,
} from './types.js';

// ---------------------------------------------------------------------------
// before_dispatch hook
// ---------------------------------------------------------------------------

/**
 * Intercepts every command dispatch before execution.
 *
 * Flow:
 *   1. Parse Authorization header → Tenant | null
 *   2. null (local) → proceed free, no metering
 *   3. Tenant found → determine layer → calculate credit cost
 *   4. Check credit balance → deduct → proceed
 *   5. Insufficient credits → return 402 Payment Required
 */
export async function beforeDispatch(
  payload: BeforeDispatchPayload,
): Promise<HookResponse> {
  let tenant = null;

  try {
    tenant = authenticateTenant(payload.headers);
  } catch (err) {
    // Parse the status code from the error message prefix "401:" or "403:"
    const msg = String(err instanceof Error ? err.message : err);
    const statusCode = msg.startsWith('401:') ? 401 : 403;
    return {
      proceed: false,
      statusCode,
      reason: msg.replace(/^\d{3}:\s*/, ''),
    };
  }

  // Local use: always free, pass through
  if (tenant === null) {
    const context: DispatchContext = {
      tenant: null,
      command: payload.command,
      layer: detectLayer(payload.command),
      creditsRequired: 0,
      startedAt: Date.now(),
    };
    return { proceed: true, context };
  }

  // Tenant use: seed credit store from resolved balance
  initTenantBalance(tenant.tenantId, tenant.creditBalance);

  const layer = detectLayer(payload.command);
  const creditsRequired = getCreditCost(payload.command, layer);

  const creditCheck = checkAndDeduct(tenant, creditsRequired);

  if (!creditCheck.allowed) {
    return {
      proceed: false,
      statusCode: creditCheck.statusCode,
      reason: creditCheck.reason ?? 'Credit check failed',
    };
  }

  const context: DispatchContext = {
    tenant,
    command: payload.command,
    layer,
    creditsRequired,
    startedAt: Date.now(),
  };

  return { proceed: true, context };
}

// ---------------------------------------------------------------------------
// after_dispatch hook
// ---------------------------------------------------------------------------

/**
 * Runs after command execution completes (success or failure).
 *
 * Flow:
 *   1. Calculate duration
 *   2. On failure: refund credits to tenant (idempotent for local)
 *   3. Log billing entry to data/billing/YYYY-MM.jsonl
 */
export async function afterDispatch(payload: AfterDispatchPayload): Promise<void> {
  const { context, success, durationMs } = payload;

  // Refund credits if command failed (tenant only)
  if (!success && context.tenant !== null && context.creditsRequired > 0) {
    refundCredits(context.tenant.tenantId, context.creditsRequired);
  }

  // Determine remaining credits for the ledger entry
  const remainingCredits =
    context.tenant !== null
      ? getBalance(context.tenant.tenantId)
      : -1; // -1 = local, unlimited

  logBillingEvent(context, durationMs, success, remainingCredits);
}

// ---------------------------------------------------------------------------
// Plugin registration object
// ---------------------------------------------------------------------------

/**
 * OpenClaw plugin manifest.
 * The hook system calls `plugin.hooks.before_dispatch` and
 * `plugin.hooks.after_dispatch` for every command dispatch.
 */
export const plugin = {
  name: 'mekong-raas',
  version: '1.0.0',
  description: 'RaaS tenant metering — credit validation and billing via OpenClaw before_dispatch hook',
  hooks: {
    before_dispatch: beforeDispatch,
    after_dispatch: afterDispatch,
  },
} as const;

export default plugin;
