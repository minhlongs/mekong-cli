/**
 * Cloud billing commands — pricing tiers, credit packs, checkout, balance
 * Uses RaaS SDK BillingResource + CreditsResource via authenticated client
 */
import type { Command } from 'commander';
import { requireCloudClient } from '../../core/raas-client.js';
import { success, error as showError, info, divider } from '../ui/output.js';

/** Open a URL in the system browser (best-effort, non-blocking) */
async function openUrl(url: string): Promise<void> {
  const { exec } = await import('node:child_process');
  exec(`open "${url}" 2>/dev/null || xdg-open "${url}" 2>/dev/null || start "" "${url}" 2>/dev/null`);
}

export function registerCloudBillingCommand(program: Command): void {
  // Use 'cloud-billing' to avoid conflict with existing 'billing' (Polar.sh) command
  const cb = program
    .command('cloud-billing')
    .description('Cloud billing — pricing tiers, credit packs, checkout, balance');

  // ── cloud-billing plans ────────────────────────────────────────────────────
  cb
    .command('plans')
    .description('Show available pricing tiers')
    .action(async () => {
      try {
        const client = requireCloudClient();
        const tiers = await client.billing.getPricing();
        info('Pricing Tiers:');
        divider();
        for (const t of tiers) {
          const credits = t.credits_per_month === -1 ? 'Unlimited' : `${t.credits_per_month}`;
          info(`${t.tier.toUpperCase()} — $${t.price_usd}/mo — ${credits} MCU/month`);
          for (const feat of t.features) {
            info(`  • ${feat}`);
          }
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  // ── cloud-billing packs ────────────────────────────────────────────────────
  cb
    .command('packs')
    .description('Show available credit packs (one-time purchase)')
    .action(async () => {
      try {
        const client = requireCloudClient();
        const packs = await client.billing.getCreditPacks();
        info('Credit Packs:');
        divider();
        for (const p of packs) {
          info(`${p.label} — ${p.credits} MCU for $${p.price_usd} [id: ${p.id}]`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  // ── cloud-billing checkout <pack-id> ──────────────────────────────────────
  cb
    .command('checkout <packId>')
    .description('Open Stripe checkout for a credit pack')
    .option('--no-open', 'Print URL instead of opening browser')
    .action(async (packId: string, opts: { open: boolean }) => {
      try {
        const client = requireCloudClient();
        const result = await client.billing.createCheckout({
          pack_id: packId,
          success_url: 'https://mekong-raas.pages.dev/?checkout=success',
          cancel_url: 'https://mekong-raas.pages.dev/?checkout=cancelled',
        });
        success(`Checkout URL: ${result.checkout_url}`);
        if (opts.open) {
          info('Opening in browser...');
          await openUrl(result.checkout_url);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  // ── credits (top-level shortcut) ──────────────────────────────────────────
  program
    .command('credits')
    .description('Check MCU credit balance')
    .action(async () => {
      try {
        const client = requireCloudClient();
        const balance = await client.credits.getBalance();
        info(`Balance:     ${balance.balance} MCU`);
        info(`Total spent: ${balance.total_spent} MCU`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
