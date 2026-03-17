/**
 * raas.ts — RaaS CLI commands for license and credit management
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerRaasCommand(program: Command, _engine: MekongEngine): void {
  const raas = program
    .command('raas')
    .description('🔑 RaaS (ROIaaS-as-a-Service) — license & credit management');

  raas
    .command('validate <tenantId> <command> [credits]')
    .description('Validate tenant license and meter credits')
    .action(async (tenantId: string, command: string, credits?: string) => {
      try {
        const { handleValidate } = await import('../../../../openclaw-engine/src/raas/raas-api.js');
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
        const { handleGetBalance } = await import('../../../../openclaw-engine/src/raas/raas-api.js');
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
        const { handleListTiers } = await import('../../../../openclaw-engine/src/raas/raas-api.js');
        const result = handleListTiers();
        if (result.ok && result.data) {
          for (const [key, tier] of Object.entries(result.data)) {
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
        const { handleRegisterTenant } = await import('../../../../openclaw-engine/src/raas/raas-api.js');
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
        const { handleOnboardTenant } = await import('../../../../openclaw-engine/src/raas/raas-onboarding.js');
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
        const { validateApiKey } = await import('../../../../openclaw-engine/src/raas/raas-onboarding.js');
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
        const { revokeApiKey } = await import('../../../../openclaw-engine/src/raas/raas-onboarding.js');
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
}
