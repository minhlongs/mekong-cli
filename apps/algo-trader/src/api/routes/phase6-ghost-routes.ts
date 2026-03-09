/**
 * Phase 6 Ghost Protocol API Routes
 *
 * ENTERPRISE-only endpoints for Ghost Protocol management.
 * Handles module status, configuration, and leverage enforcement.
 */

import * as fs from 'fs';
import * as path from 'path';
import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { LicenseService, LicenseTier } from '../../lib/raas-gate';
import { licenseAuthPlugin } from '../middleware/license-auth-middleware';
import { checkLeverageCap, TIER_LEVERAGE_CAPS } from '../../execution/max-order-limits';

/** Request body for leverage validation */
interface LeverageCheckBody {
  leverage: number;
}

/** Request body for Phase 6 config update (ephemeral — runtime only) */
interface Phase6ConfigUpdateBody {
  polymorphicMatrix?: { enabled: boolean };
  wsSharding?: { enabled: boolean };
  chameleon?: { enabled: boolean };
}

/** Cached config — loaded once at startup, updated in-memory via PUT */
let cachedConfig: Record<string, Record<string, unknown>> | null = null;

/** Load Phase 6 config from file (cached after first read) */
function loadPhase6Config(): Record<string, Record<string, unknown>> {
  if (cachedConfig) return cachedConfig;

  const defaultConfig = {
    polymorphicMatrix: { enabled: false },
    wsSharding: { enabled: false },
    chameleon: { enabled: false },
  };

  try {
    const configPath = path.join(__dirname, '..', '..', '..', 'config.phase6.json');
    cachedConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    return cachedConfig!;
  } catch {
    cachedConfig = defaultConfig;
    return cachedConfig;
  }
}

/**
 * Build Phase 6 Ghost Protocol routes — ENTERPRISE tier required
 */
export function buildPhase6Routes(): (fastify: FastifyInstance) => Promise<void> {
  return async (fastify: FastifyInstance) => {
    // Gate all routes behind ENTERPRISE license
    await fastify.register(licenseAuthPlugin, {
      requiredTier: LicenseTier.ENTERPRISE,
    });

    // GET /api/v1/phase6/status — Ghost Protocol module status
    fastify.get('/api/v1/phase6/status', async (_request: FastifyRequest, reply: FastifyReply) => {
      const config = loadPhase6Config();
      return reply.send({
        phase: 6,
        codename: 'Ghost Protocol',
        modules: {
          polymorphicMatrix: { enabled: config.polymorphicMatrix?.enabled ?? false },
          wsSharding: { enabled: config.wsSharding?.enabled ?? false },
          chameleon: { enabled: config.chameleon?.enabled ?? false },
        },
        leverageCaps: TIER_LEVERAGE_CAPS,
      });
    });

    // POST /api/v1/phase6/leverage/check — validate leverage against caller's license tier
    fastify.post('/api/v1/phase6/leverage/check', async (request: FastifyRequest, reply: FastifyReply) => {
      const body = request.body as LeverageCheckBody;

      if (!body || typeof body.leverage !== 'number' || body.leverage < 1) {
        return reply.status(400).send({
          error: 'Invalid Request',
          message: 'leverage must be a positive number >= 1',
        });
      }

      // Use server-side tier from LicenseService — never trust client input
      const tier = LicenseService.getInstance().getTier();
      const result = checkLeverageCap(body.leverage, tier);

      return reply.status(result.passed ? 200 : 403).send(result);
    });

    // PUT /api/v1/phase6/config — update Ghost Protocol module toggles (ephemeral, runtime only)
    fastify.put('/api/v1/phase6/config', async (request: FastifyRequest, reply: FastifyReply) => {
      const body = request.body as Phase6ConfigUpdateBody;

      if (!body || typeof body !== 'object') {
        return reply.status(400).send({
          error: 'Invalid Request',
          message: 'Request body must be an object with module toggles',
        });
      }

      // Update in-memory cache (ephemeral — does NOT persist to disk)
      const config = loadPhase6Config();
      cachedConfig = {
        ...config,
        polymorphicMatrix: {
          ...config.polymorphicMatrix,
          ...(body.polymorphicMatrix && { enabled: body.polymorphicMatrix.enabled }),
        },
        wsSharding: {
          ...config.wsSharding,
          ...(body.wsSharding && { enabled: body.wsSharding.enabled }),
        },
        chameleon: {
          ...config.chameleon,
          ...(body.chameleon && { enabled: body.chameleon.enabled }),
        },
      };

      return reply.send({
        message: 'Phase 6 configuration updated (runtime only, not persisted)',
        config: cachedConfig,
      });
    });

    // GET /api/v1/phase6/leverage/caps — get tier leverage caps
    fastify.get('/api/v1/phase6/leverage/caps', async (_request: FastifyRequest, reply: FastifyReply) => {
      return reply.send({
        caps: TIER_LEVERAGE_CAPS,
        maxGlobal: 20,
        description: 'Maximum leverage by license tier',
      });
    });
  };
}

/** Reset cached config (for testing) */
export function resetPhase6ConfigCache(): void {
  cachedConfig = null;
}
