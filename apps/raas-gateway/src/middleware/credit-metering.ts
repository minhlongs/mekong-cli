/**
 * Credit Metering Middleware — Deduct credits per API call
 *
 * Applied after auth + rate limiting, before route handler
 */

import type { MiddlewareHandler } from 'hono';
import type { Env } from '../index';
import { getTenant } from './auth';
import { CreditService, MISSION_COSTS } from '../services/credit-service';
import { PaymentRequiredError } from '../utils/errors';
import { json } from '../utils/response';

interface CreditMeteringOptions {
  /** Credit cost for this endpoint (default: 1) */
  cost?: number;
  /** Skip metering for certain tiers */
  exemptTiers?: string[];
  /** Custom description for transaction */
  description?: string;
}

/**
 * Credit metering middleware factory
 * Deducts credits before allowing request to proceed
 */
export function creditMetering(
  options: CreditMeteringOptions = {}
): MiddlewareHandler<{ Bindings: Env }> {
  return async (c, next) => {
    const tenant = getTenant(c);
    const creditService = new CreditService(c.env);

    // Check tier exemption
    if (options.exemptTiers?.includes(tenant.tier)) {
      await next();
      return;
    }

    // Get credit cost
    const cost = options.cost ?? 1;

    // Skip if free
    if (cost <= 0) {
      await next();
      return;
    }

    // Check balance first
    const hasCredits = await creditService.hasSufficientCredits(tenant.tenantId, cost);
    if (!hasCredits) {
      const balance = await creditService.getBalance(tenant.tenantId);

      return json(
        {
          error: 'Insufficient credits',
          code: 'INSUFFICIENT_CREDITS',
          required: cost,
          available: balance,
          message: `Required: ${cost} credits, Available: ${balance} credits. Please purchase more credits.`,
        },
        { status: 402 }
      );
    }

    // Deduct credits
    const result = await creditService.deduct(
      tenant.tenantId,
      cost,
      'mission',
      options.description || `API call: ${c.req.method} ${c.req.path}`,
      undefined
    );

    if (!result.success) {
      if (result.error === 'INSUFFICIENT_CREDITS') {
        return json(
          {
            error: 'Insufficient credits',
            code: 'INSUFFICIENT_CREDITS',
            required: cost,
            available: result.balance || 0,
          },
          { status: 402 }
        );
      }
      return json(
        { error: 'Credit metering failed', code: 'METERING_ERROR' },
        { status: 500 }
      );
    }

    // Set credit headers
    c.header('X-Credit-Cost', cost.toString());
    c.header('X-Credit-Balance', (result.balance || 0).toString());

    await next();
  };
}

/**
 * Get credit cost for mission complexity
 */
export function getMissionCost(complexity: 'simple' | 'standard' | 'complex'): number {
  return MISSION_COSTS[complexity] || MISSION_COSTS.standard;
}
