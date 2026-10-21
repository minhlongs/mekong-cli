/**
 * raas-loaders.ts — Dynamic module loaders and status/health actions for RaaS CLI commands
 */
import { success, error as showError, info } from '../ui/output.js';

export async function getRaasApiModules() {
  const mod = await import('@openclaw/engine/raas/raas-api.js');
  const { handleValidate, handleGetBalance, handleListTiers, handleRegisterTenant, handleGetUsage } = mod;
  return { handleValidate, handleGetBalance, handleListTiers, handleRegisterTenant, handleGetUsage };
}

export async function getRaasOnboardingModules() {
  const mod = await import('@openclaw/engine/raas/raas-onboarding.js');
  const { handleOnboardTenant, validateApiKey, revokeApiKey } = mod;
  return { handleOnboardTenant, validateApiKey, revokeApiKey };
}

export async function getRaasBillingModules() {
  const mod = await import('@openclaw/engine/raas/raas-billing');
  const { getUsageAnalytics } = mod;
  return { getUsageAnalytics };
}

export async function getRaasRateLimiterModules() {
  const mod = await import('@openclaw/engine/raas/raas-rate-limiter');
  const { getRateLimitStatus } = mod;
  return { getRateLimitStatus };
}

export async function getRaasHealthModules() {
  const mod = await import('@openclaw/engine/raas/raas-health');
  const { checkHealth } = mod;
  return { checkHealth };
}

export async function runRaasStatus(tenantId: string): Promise<void> {
  try {
    const { getUsageAnalytics } = await getRaasBillingModules();
    const { getRateLimitStatus } = await getRaasRateLimiterModules();
    const { checkHealth } = await getRaasHealthModules();
    const { handleGetBalance } = await getRaasApiModules();

    const bal = handleGetBalance(tenantId);
    if (!bal.ok || !bal.data) {
      showError(bal.error ?? 'Tenant not found');
      process.exitCode = 1;
      return;
    }
    info(`── Tenant: ${tenantId} ──`);
    info(`Tier: ${bal.data.tier}`);
    info(`Credits: ${bal.data.used}/${bal.data.limit === -1 ? '∞' : bal.data.limit} (${bal.data.remaining} remaining)`);

    const analytics = getUsageAnalytics(tenantId);
    if (analytics.ok && analytics.data) {
      const a = analytics.data;
      info(`Calls: ${a.totalCalls} total, ${a.successfulCalls} success, ${a.throttledCount} throttled`);
      info(`Avg latency: ${a.avgLatencyMs}ms`);
    }

    const rl = getRateLimitStatus(tenantId, bal.data.tier);
    info(`Rate limit: ${rl.tokens}/${rl.maxTokens} tokens`);

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
}

export async function runRaasHealth(): Promise<void> {
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
}
