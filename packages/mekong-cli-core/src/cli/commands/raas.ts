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
}
