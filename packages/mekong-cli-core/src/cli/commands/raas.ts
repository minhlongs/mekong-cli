/**
 * raas.ts — RaaS CLI commands for license and credit management
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

// Dynamic imports to avoid TypeScript module resolution issues
async function getRaasApiModules() {
  const mod = await import('@openclaw/engine/raas/raas-api.js');
  const { handleValidate, handleGetBalance, handleListTiers, handleRegisterTenant, handleGetUsage } = mod;
  return { handleValidate, handleGetBalance, handleListTiers, handleRegisterTenant, handleGetUsage };
}

async function getRaasOnboardingModules() {
  const mod = await import('@openclaw/engine/raas/raas-onboarding.js');
  const { handleOnboardTenant, validateApiKey, revokeApiKey } = mod;
  return { handleOnboardTenant, validateApiKey, revokeApiKey };
}

async function getRaasBillingModules() {
  const mod = await import('@openclaw/engine/raas/raas-billing');
  const { getUsageAnalytics } = mod;
  return { getUsageAnalytics };
}

async function getRaasRateLimiterModules() {
  const mod = await import('@openclaw/engine/raas/raas-rate-limiter');
  const { getRateLimitStatus } = mod;
  return { getRateLimitStatus };
}

async function getRaasHealthModules() {
  const mod = await import('@openclaw/engine/raas/raas-health');
  const { checkHealth } = mod;
  return { checkHealth };
}

export function registerRaasCommand(program: Command, _engine: MekongEngine): void {
  const raas = program
    .command('raas')
    .description('🔑 RaaS (ROIaaS-as-a-Service) — license & credit management');

  raas
    .command('validate <tenantId> <command> [credits]')
    .description('Validate tenant license and meter credits')
    .action(async (tenantId: string, command: string, credits?: string) => {
      try {
        const { handleValidate } = await getRaasApiModules();
        const cost = credits ? parseInt(credits, 10) : 1;
        const result = handleValidate(tenantId, command, cost);
        if (result.ok) {
          success(`✅ Validated: ${command} (${cost} MCU deducted)`);
          info(`Remaining: ${result.data?.remainingCredits} credits`);
        } else {
          showError(`❌ ${result.error}`);
          process.exitCode = 1;
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  raas
    .command('balance <tenantId>')
    .description('Check credit balance for a tenant')
    .action(async (tenantId: string) => {
      try {
        const { handleGetBalance } = await getRaasApiModules();
        const result = handleGetBalance(tenantId);
        if (result.ok && result.data) {
          info(`Tier: ${result.data.tier}`);
          info(`Used: ${result.data.used} / ${result.data.limit === -1 ? '∞' : result.data.limit}`);
          info(`Remaining: ${result.data.remaining}`);
        } else {
          showError(result.error ?? 'Unknown error');
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
      }
    });

  raas
    .command('tiers')
    .description('List available pricing tiers')
    .action(async () => {
      try {
        const { handleListTiers } = await getRaasApiModules();
        const result = handleListTiers();
        if (result.ok && result.data) {
          const tiers = result.data as Record<string, { priceUsd: number; creditsPerMonth: number; maxProjects: number }>;
          for (const [key, tier] of Object.entries(tiers)) {
            info(`${key}: $${tier.priceUsd}/mo — ${tier.creditsPerMonth === -1 ? '∞' : tier.creditsPerMonth} credits, ${tier.maxProjects === -1 ? '∞' : tier.maxProjects} projects`);
          }
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
      }
    });

  raas
    .command('register <tenantId> <tier>')
    .description('Register a new tenant with a tier')
    .action(async (tenantId: string, tier: string) => {
      try {
        const { handleRegisterTenant } = await getRaasApiModules();
        const result = handleRegisterTenant({
          tenantId,
          tier: tier as 'starter' | 'pro' | 'enterprise',
          active: true,
          expiresAt: Date.now() + 30 * 86400000, // 30 days
          usedCredits: 0,
        });
        if (result.ok) {
          success(`Tenant "${tenantId}" registered on ${tier} tier`);
        } else {
          showError(result.error ?? 'Registration failed');
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
      }
    });

  raas
    .command('onboard <tenantId> <tier> <email>')
    .description('Full onboarding: register tenant + generate API key')
    .action(async (tenantId: string, tier: string, email: string) => {
      try {
        const { handleOnboardTenant } = await getRaasOnboardingModules();
        const result = handleOnboardTenant({
          tenantId,
          tier: tier as 'starter' | 'pro' | 'enterprise',
          email,
        });
        if (result.ok && result.data) {
          success(`✅ Tenant "${tenantId}" onboarded on ${tier} tier`);
          info(`API Key: ${result.data.apiKey}`);
          info(`Credits: ${result.data.creditsPerMonth === -1 ? '∞' : result.data.creditsPerMonth}/month`);
          info(`Expires: ${new Date(result.data.expiresAt).toISOString()}`);
        } else {
          showError(result.error ?? 'Onboarding failed');
          process.exitCode = 1;
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  raas
    .command('api-key-validate <apiKey>')
    .description('Validate an API key')
    .action(async (apiKey: string) => {
      try {
        const { validateApiKey } = await getRaasOnboardingModules();
        const result = validateApiKey(apiKey);
        if (result.ok && result.data) {
          success(`✅ Valid — tenant: ${result.data.tenantId}, tier: ${result.data.tier}`);
        } else {
          showError(result.error ?? 'Invalid key');
          process.exitCode = 1;
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  raas
    .command('api-key-revoke <apiKey>')
    .description('Revoke an API key')
    .action(async (apiKey: string) => {
      try {
        const { revokeApiKey } = await getRaasOnboardingModules();
        const result = revokeApiKey(apiKey);
        if (result.ok) {
          success('✅ API key revoked');
        } else {
          showError(result.error ?? 'Revoke failed');
          process.exitCode = 1;
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  raas
    .command('status <tenantId>')
    .description('Show tenant status: credits, rate limits, health')
    .action(async (tenantId: string) => {
      try {
        const { getUsageAnalytics } = await getRaasBillingModules();
        const { getRateLimitStatus } = await getRaasRateLimiterModules();
        const { checkHealth } = await getRaasHealthModules();

        // Balance
        const { handleGetBalance } = await getRaasApiModules();
        const bal = handleGetBalance(tenantId);
        if (!bal.ok) {
          showError(bal.error ?? 'Tenant not found');
          process.exitCode = 1;
          return;
        }
        info(`── Tenant: ${tenantId} ──`);
        info(`Tier: ${bal.data!.tier}`);
        info(`Credits: ${bal.data!.used}/${bal.data!.limit === -1 ? '∞' : bal.data!.limit} (${bal.data!.remaining} remaining)`);

        // Analytics
        const analytics = getUsageAnalytics(tenantId);
        if (analytics.ok && analytics.data) {
          const a = analytics.data;
          info(`Calls: ${a.totalCalls} total, ${a.successfulCalls} success, ${a.throttledCount} throttled`);
          info(`Avg latency: ${a.avgLatencyMs}ms`);
        }

        // Rate limit
        const rl = getRateLimitStatus(tenantId, bal.data!.tier);
        info(`Rate limit: ${rl.tokens}/${rl.maxTokens} tokens`);

        // Health
        const health = checkHealth();
        if (health.ok && health.data) {
          const comps = health.data.components.map(c => `${c.name}:${c.status}`).join(' ');
          info(`Health: ${health.data.status} [${comps}]`);
          info(`Uptime: ${Math.round(health.data.uptime / 1000)}s | v${health.data.version}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  raas
    .command('health')
    .description('RaaS system health check')
    .action(async () => {
      try {
        const { checkHealth } = await getRaasHealthModules();
        const result = checkHealth();
        if (result.ok && result.data) {
          success(`Status: ${result.data.status} | v${result.data.version}`);
          for (const c of result.data.components) {
            info(`  ${c.name}: ${c.status}${c.message ? ` — ${c.message}` : ''}`);
          }
          info(`Uptime: ${Math.round(result.data.uptime / 1000)}s`);
        } else {
          showError('Health check failed');
          process.exitCode = 1;
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
