/**
 * `mekong billing` — Billing and subscription management subcommands.
 *
 *   mekong billing status          Show current subscription from NOWPayments
 *   mekong billing receipts        List local payment receipt history
 *   mekong billing webhook-test    Simulate a webhook payload for local dev
 */
import type { Command } from 'commander';
import { ReceiptStore } from '../../payments/receipt-store.js';
import { createNowPaymentsClientFromEnv } from '../../payments/nowpayments-client.js';
import { resolveTierFromProduct } from '../../payments/types.js';
import { DEFAULT_RECEIPT_PATH, runWebhookTest } from './billing-helpers.js';

export function registerBillingCommand(program: Command): void {
  const billing = program
    .command('billing')
    .description('Billing and subscription management (NOWPayments)');

  // ── billing status ──────────────────────────────────────────────────────────
  billing
    .command('status')
    .description('Show current subscription status from NOWPayments')
    .option('--customer <id>', 'Customer ID or email to check')
    .action(async (opts: { customer?: string }) => {
      const clientResult = createNowPaymentsClientFromEnv();
      if (!clientResult.ok) {
        console.error(`Error: ${clientResult.error.message}`);
        console.error('Set NOWPAYMENTS_API_KEY environment variable to use billing status.');
        process.exit(1);
      }

      const customerId = opts.customer ?? process.env['NOWPAYMENTS_CUSTOMER_ID'];
      if (!customerId) {
        console.error('Error: specify --customer <id> or set NOWPAYMENTS_CUSTOMER_ID env var.');
        process.exit(1);
      }

      const result = await clientResult.value.checkSubscription(customerId);
      if (!result.ok) {
        console.error('Failed to check subscription:', result.error.message);
        process.exit(1);
      }

      const { active, subscription } = result.value;
      console.log('\nBilling Status');
      console.log(`  Customer   : ${customerId}`);
      console.log(`  Active     : ${active}`);
      if (subscription) {
        console.log(`  Status     : ${subscription.status}`);
        console.log(`  Product    : ${subscription.product_id}`);
        console.log(`  Tier       : ${resolveTierFromProduct(subscription.product_id)}`);
        console.log(`  Period end : ${subscription.current_period_end}`);
        if (subscription.cancel_at_period_end) {
          console.log('  Note       : Cancels at period end');
        }
      } else {
        console.log('  Note       : No active subscription found');
      }
      console.log('');
    });

  // ── billing receipts ────────────────────────────────────────────────────────
  billing
    .command('receipts')
    .description('List local payment receipt history')
    .option('--customer <id>', 'Filter by customer ID or email')
    .option('--from <date>', 'Filter from date (ISO 8601)')
    .option('--to <date>', 'Filter to date (ISO 8601)')
    .option('--limit <n>', 'Max number of receipts to show', '20')
    .action(async (opts: { customer?: string; from?: string; to?: string; limit: string }) => {
      const store = new ReceiptStore(DEFAULT_RECEIPT_PATH);

      let result;
      if (opts.customer) {
        result = await store.findByCustomer(opts.customer);
      } else if (opts.from || opts.to) {
        const from = opts.from ?? '1970-01-01T00:00:00Z';
        const to = opts.to ?? new Date().toISOString();
        result = await store.findByDateRange(from, to);
      } else {
        result = await store.readAll();
      }

      if (!result.ok) {
        console.error('Failed to read receipts:', result.error.message);
        process.exit(1);
      }

      const limit = Math.max(1, parseInt(opts.limit, 10) || 20);
      const events = result.value.slice(-limit);

      if (events.length === 0) {
        console.log('\nNo payment receipts found.\n');
        return;
      }

      console.log(`\nPayment Receipts (${events.length} shown)\n`);
      for (const e of events) {
        const status = e.processed ? (e.error === 'duplicate' ? 'dup' : 'ok') : 'err';
        const tier = e.tier ? `  tier=${e.tier}` : '';
        const key = e.licenseKey ? `  key=${e.licenseKey.slice(0, 20)}...` : '';
        const errMsg = e.error && e.error !== 'duplicate' ? `  error=${e.error}` : '';
        console.log(
          `  [${e.receivedAt}] ${e.type.padEnd(28)} ${status}  customer=${e.customerId ?? e.customerEmail ?? 'unknown'}${tier}${key}${errMsg}`,
        );
      }
      console.log('');
    });

  // ── billing webhook-test ────────────────────────────────────────────────────
  billing
    .command('webhook-test')
    .description('Simulate a webhook payload for local development')
    .option('--event <type>', 'Event type to simulate', 'checkout.completed')
    .option('--product <id>', 'Product ID', 'prod_starter_monthly')
    .option('--email <email>', 'Customer email', 'test@example.com')
    .option('--customer-id <id>', 'Customer ID', 'cust_test_001')
    .option(
      '--secret <secret>',
      'Webhook secret (default: NOWPAYMENTS_WEBHOOK_SECRET env)',
    )
    .option('--dry-run', 'Print payload without processing', false)
    .action(runWebhookTest);
}
