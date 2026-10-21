/**
 * billing-helpers.ts — Webhook test payload builder and simulation helper for billing CLI.
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import { WebhookHandler } from '../../payments/webhook-handler.js';
import type { WebhookEventType } from '../../payments/types.js';

export const DEFAULT_RECEIPT_PATH = join(homedir(), '.mekong', 'payments', 'receipts.jsonl');
export const DEFAULT_REGISTRY = join(homedir(), '.mekong', 'admin', 'keys.json');
export const DEFAULT_AUDIT_LOG = join(homedir(), '.mekong', 'admin', 'audit.jsonl');

export function buildTestPayload(
  type: WebhookEventType,
  productId: string,
  email: string,
  customerId: string,
) {
  const id = `evt_test_${Date.now()}`;
  const now = new Date().toISOString();

  if (type === 'checkout.completed') {
    return {
      type,
      id,
      created_at: now,
      data: {
        id: `chk_test_${Date.now()}`,
        status: 'succeeded',
        customer_email: email,
        customer_id: customerId,
        product_id: productId,
        amount: 4900,
        currency: 'usd',
        metadata: {},
      },
    };
  }

  return {
    type,
    id,
    created_at: now,
    data: {
      id: `sub_test_${Date.now()}`,
      status: type.includes('cancel') ? 'canceled' : 'active',
      customer_id: customerId,
      customer_email: email,
      product_id: productId,
      current_period_start: now,
      current_period_end: new Date(Date.now() + 30 * 86_400_000).toISOString(),
      cancel_at_period_end: type.includes('cancel'),
      metadata: {},
    },
  };
}

export async function runWebhookTest(opts: {
  event: string;
  product: string;
  email: string;
  customerId: string;
  secret?: string;
  dryRun: boolean;
}): Promise<void> {
  const eventType = opts.event as WebhookEventType;
  const payload = buildTestPayload(eventType, opts.product, opts.email, opts.customerId);
  const rawBody = JSON.stringify(payload);

  console.log('\nWebhook Test Payload:');
  console.log(JSON.stringify(payload, null, 2));

  if (opts.dryRun) {
    console.log('\n[dry-run] Payload printed. Not processed.\n');
    return;
  }

  const secret =
    opts.secret ?? process.env['NOWPAYMENTS_WEBHOOK_SECRET'] ?? 'test-webhook-secret';
  const webhookId = `test_${Date.now()}`;
  const timestamp = String(Math.floor(Date.now() / 1000));

  const { createHmac } = await import('node:crypto');
  const signedContent = `${webhookId}.${timestamp}.${rawBody}`;
  const sigHex = createHmac('sha256', secret).update(signedContent).digest('hex');
  const signature = `v1,${sigHex}`;

  const handler = new WebhookHandler({
    secret,
    registryPath: DEFAULT_REGISTRY,
    auditLogPath: DEFAULT_AUDIT_LOG,
    receiptStorePath: DEFAULT_RECEIPT_PATH,
  });

  const result = await handler.process({
    rawBody,
    signature,
    webhookId,
    timestamp,
  });

  if (!result.ok) {
    console.error('\nWebhook processing failed:', result.error.message);
    process.exit(1);
  }

  const event = result.value;
  console.log('\nWebhook processed:');
  console.log(`  Event ID  : ${event.id}`);
  console.log(`  Type      : ${event.type}`);
  console.log(`  Processed : ${event.processed}`);
  if (event.licenseKey) console.log(`  License   : ${event.licenseKey}`);
  if (event.tier) console.log(`  Tier      : ${event.tier}`);
  if (event.error && event.error !== 'duplicate') console.log(`  Error     : ${event.error}`);
  console.log('');
}
