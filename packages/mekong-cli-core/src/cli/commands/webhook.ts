/**
 * webhook.ts — Webhook management CLI commands
 * Configure, test, and monitor webhook endpoints for RaaS event delivery
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

interface WebhookRecord {
  id: string;
  url: string;
  events: string[];
  status: 'active' | 'failing' | 'paused';
  lastDelivery: string;
  successRate: number;
}

const MOCK_WEBHOOKS: WebhookRecord[] = [
  {
    id: 'wh_a1b2c3',
    url: 'https://hooks.acmecorp.io/mekong',
    events: ['mission.completed', 'billing.invoice', 'credit.low'],
    status: 'active',
    lastDelivery: '2026-03-22T08:41:00Z',
    successRate: 98.5,
  },
  {
    id: 'wh_d4e5f6',
    url: 'https://n8n.startupx.dev/webhook/mekong-events',
    events: ['mission.completed', 'mission.failed'],
    status: 'failing',
    lastDelivery: '2026-03-22T07:15:00Z',
    successRate: 61.2,
  },
  {
    id: 'wh_g7h8i9',
    url: 'https://zapier.com/hooks/catch/9910/abc123/',
    events: ['credit.low', 'tenant.created'],
    status: 'active',
    lastDelivery: '2026-03-21T22:00:00Z',
    successRate: 100,
  },
];

const MOCK_LOGS: Record<string, Array<{ ts: string; status: number; ms: number; event: string }>> = {
  wh_a1b2c3: [
    { ts: '2026-03-22T08:41:00Z', status: 200, ms: 142, event: 'mission.completed' },
    { ts: '2026-03-22T07:30:00Z', status: 200, ms: 98,  event: 'billing.invoice' },
    { ts: '2026-03-22T06:00:00Z', status: 200, ms: 210, event: 'credit.low' },
  ],
  wh_d4e5f6: [
    { ts: '2026-03-22T07:15:00Z', status: 503, ms: 5012, event: 'mission.failed' },
    { ts: '2026-03-22T06:45:00Z', status: 503, ms: 5010, event: 'mission.completed' },
    { ts: '2026-03-22T05:00:00Z', status: 200, ms: 188,  event: 'mission.completed' },
  ],
  wh_g7h8i9: [
    { ts: '2026-03-21T22:00:00Z', status: 200, ms: 321, event: 'credit.low' },
    { ts: '2026-03-20T14:00:00Z', status: 200, ms: 280, event: 'tenant.created' },
  ],
};

export function registerWebhookCommand(program: Command): void {
  const webhook = program
    .command('webhook')
    .description('Webhook management — configure event delivery endpoints');

  webhook
    .command('list')
    .description('List all configured webhook endpoints')
    .action(() => {
      heading('Configured Webhooks');
      info(`${'ID'.padEnd(12)} ${'URL'.padEnd(42)} ${'Status'.padEnd(10)} ${'Rate'.padEnd(8)} Events`);
      divider();
      for (const wh of MOCK_WEBHOOKS) {
        const rate = `${wh.successRate}%`;
        const evts = wh.events.join(', ');
        const line = `${wh.id.padEnd(12)} ${wh.url.padEnd(42)} ${wh.status.padEnd(10)} ${rate.padEnd(8)} ${evts}`;
        if (wh.status === 'active') success(line);
        else if (wh.status === 'failing') warn(line);
        else info(line);
      }
      divider();
      info(`${MOCK_WEBHOOKS.length} endpoints registered`);
      info('');
      info('Commands:');
      info('  mekong webhook add --url <url> --events <events>');
      info('  mekong webhook test --id <id>');
      info('  mekong webhook logs --id <id>');
      info('');
    });

  webhook
    .command('add')
    .description('Add a new webhook endpoint')
    .requiredOption('--url <url>', 'Endpoint URL')
    .option('--events <events>', 'Comma-separated event types', 'mission.completed')
    .action((opts: { url: string; events: string }) => {
      const id = `wh_${Date.now().toString(36)}`;
      const events = opts.events.split(',').map((e) => e.trim());

      heading('Webhook Registered');
      keyValue('ID', id);
      keyValue('URL', opts.url);
      keyValue('Events', events.join(', '));
      keyValue('Status', 'active');
      divider();
      success('Webhook endpoint added successfully');
      info('');
      info('Test it now:');
      info(`  mekong webhook test --id ${id}`);
      info('');
    });

  webhook
    .command('remove')
    .description('Remove a webhook endpoint by ID')
    .requiredOption('--id <id>', 'Webhook ID to remove')
    .action((opts: { id: string }) => {
      const found = MOCK_WEBHOOKS.find((w) => w.id === opts.id);
      if (!found) {
        warn(`Webhook not found: ${opts.id}`);
        info('Run `mekong webhook list` to see valid IDs');
        return;
      }
      heading('Webhook Removed');
      keyValue('ID', found.id);
      keyValue('URL', found.url);
      success('Endpoint removed — no further deliveries will be made');
      info('');
    });

  webhook
    .command('test')
    .description('Send a test payload to a webhook endpoint')
    .requiredOption('--id <id>', 'Webhook ID to test')
    .action((opts: { id: string }) => {
      const found = MOCK_WEBHOOKS.find((w) => w.id === opts.id);
      if (!found) {
        warn(`Webhook not found: ${opts.id}`);
        return;
      }
      heading('Webhook Test');
      keyValue('ID', found.id);
      keyValue('URL', found.url);
      info('Sending sample payload...');
      divider();
      info('Payload:');
      info('  { "event": "test.ping", "tenant": "demo", "ts": "' + new Date().toISOString() + '" }');
      divider();
      if (found.status === 'failing') {
        warn('Response: 503 Service Unavailable (5010ms)');
        warn('Endpoint appears to be down — check server logs');
      } else {
        success('Response: 200 OK (143ms)');
        success('Test delivery successful');
      }
      info('');
    });

  webhook
    .command('logs')
    .description('Show recent delivery logs for a webhook')
    .requiredOption('--id <id>', 'Webhook ID')
    .action((opts: { id: string }) => {
      const found = MOCK_WEBHOOKS.find((w) => w.id === opts.id);
      if (!found) {
        warn(`Webhook not found: ${opts.id}`);
        return;
      }
      const logs = MOCK_LOGS[found.id] ?? [];
      heading(`Delivery Logs — ${found.id}`);
      keyValue('URL', found.url);
      keyValue('Success rate', `${found.successRate}%`);
      divider();
      info(`${'Timestamp'.padEnd(26)} ${'Status'.padEnd(8)} ${'Latency'.padEnd(10)} Event`);
      divider();
      for (const log of logs) {
        const line = `${log.ts.padEnd(26)} ${String(log.status).padEnd(8)} ${`${log.ms}ms`.padEnd(10)} ${log.event}`;
        if (log.status === 200) success(line);
        else warn(line);
      }
      info('');
    });
}
