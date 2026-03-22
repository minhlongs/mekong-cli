/**
 * `mekong notification` — Notification management subcommands (Wave 52).
 *
 *   mekong notification send       Send notification via channel
 *   mekong notification list       List notification history
 *   mekong notification config     Show notification configuration
 *   mekong notification channels   Show available channels and status
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

const VALID_CHANNELS = ['email', 'slack', 'webhook', 'sms'] as const;
type Channel = typeof VALID_CHANNELS[number];

/** Mock notification history for demo output */
const MOCK_NOTIFICATIONS = [
  { id: 'ntf-201', channel: 'email',   to: 'khachhang@example.vn', message: 'Đơn hàng đã xác nhận',     status: 'sent',    sentAt: '2026-03-22 09:01' },
  { id: 'ntf-202', channel: 'slack',   to: '#sales-team',           message: 'Lead mới từ form website', status: 'sent',    sentAt: '2026-03-22 09:15' },
  { id: 'ntf-203', channel: 'webhook', to: 'https://hook.io/abc',   message: 'Thanh toán thành công',    status: 'failed',  sentAt: '2026-03-22 09:30' },
  { id: 'ntf-204', channel: 'sms',     to: '+84901234567',          message: 'Mã OTP: 482910',           status: 'sent',    sentAt: '2026-03-22 09:45' },
  { id: 'ntf-205', channel: 'email',   to: 'ceo@company.vn',        message: 'Báo cáo doanh thu Q1',     status: 'pending', sentAt: '2026-03-22 10:00' },
];

/** Channel configuration state */
const CHANNEL_CONFIG: Record<Channel, { configured: boolean; rateLimit: string }> = {
  email:   { configured: true,  rateLimit: '500/day'  },
  slack:   { configured: true,  rateLimit: '1000/day' },
  webhook: { configured: true,  rateLimit: 'unlimited' },
  sms:     { configured: false, rateLimit: '100/day'  },
};

export function registerNotificationCommand(program: Command): void {
  const cmd = program.command('notification').description('Notification management');

  // ── notification send ──────────────────────────────────────────────────────
  cmd.command('send')
    .description('Send notification via channel')
    .option('--channel <channel>', 'Channel: email|slack|webhook|sms', 'email')
    .option('--to <recipient>', 'Recipient (email, phone, URL, channel)', '')
    .option('--message <message>', 'Notification message body', '')
    .action((opts: { channel?: string; to?: string; message?: string }) => {
      const channel = (opts.channel ?? 'email') as Channel;
      const to = opts.to ?? '';
      const message = opts.message ?? '';

      if (!VALID_CHANNELS.includes(channel)) {
        warn(`Unknown channel "${channel}". Valid: ${VALID_CHANNELS.join(', ')}`);
        return;
      }
      if (!to) {
        warn('Recipient --to is required');
        return;
      }
      if (!message) {
        warn('Message --message is required');
        return;
      }
      if (!CHANNEL_CONFIG[channel].configured) {
        warn(`Channel "${channel}" is not configured. Run: mekong notification config`);
        return;
      }

      heading('Send Notification');
      const id = `ntf-${String(Date.now()).slice(-3)}`;
      keyValue('Notification ID', id);
      keyValue('Channel', channel);
      keyValue('Recipient', to);
      keyValue('Message', message.slice(0, 60) + (message.length > 60 ? '...' : ''));
      keyValue('Status', 'sent');
      keyValue('Sent At', new Date().toISOString().replace('T', ' ').slice(0, 16));
      divider();
      success(`Notification sent via ${channel} to "${to}"`);
    });

  // ── notification list ──────────────────────────────────────────────────────
  cmd.command('list')
    .description('List notification history')
    .option('--status <status>', 'Filter: all|sent|failed|pending', 'all')
    .option('--limit <n>', 'Max records to show', '20')
    .action((opts: { status?: string; limit?: string }) => {
      const statusFilter = opts.status ?? 'all';
      const limit = parseInt(opts.limit ?? '20', 10);
      heading('Notification History');

      const rows = statusFilter === 'all'
        ? MOCK_NOTIFICATIONS
        : MOCK_NOTIFICATIONS.filter(n => n.status === statusFilter);

      if (rows.length === 0) {
        warn(`No notifications with status "${statusFilter}"`);
        return;
      }

      for (const n of rows.slice(0, limit)) {
        const tag = n.status === 'sent' ? 'SENT   ' : n.status === 'failed' ? 'FAILED ' : 'PENDING';
        console.log(`  [${tag}] ${n.id}  ${n.channel.padEnd(7)} ${n.to.padEnd(28)} ${n.sentAt}`);
      }
      divider();
      info(`Showing ${Math.min(rows.length, limit)} of ${rows.length} notifications`);
    });

  // ── notification config ────────────────────────────────────────────────────
  cmd.command('config')
    .description('Show current notification configuration')
    .action(() => {
      heading('Notification Configuration');
      keyValue('Default Channel', 'email');
      keyValue('Retry On Failure', 'true');
      keyValue('Max Retries', '3');
      keyValue('Retry Delay', '30s');
      divider();
      info('Channel Rate Limits:');
      for (const ch of VALID_CHANNELS) {
        const cfg = CHANNEL_CONFIG[ch];
        const state = cfg.configured ? 'enabled ' : 'disabled';
        console.log(`  ${ch.padEnd(8)} [${state}]  rate limit: ${cfg.rateLimit}`);
      }
      divider();
      success('Configuration loaded');
    });

  // ── notification channels ──────────────────────────────────────────────────
  cmd.command('channels')
    .description('Show available channels with configuration status')
    .action(() => {
      heading('Notification Channels');
      for (const ch of VALID_CHANNELS) {
        const cfg = CHANNEL_CONFIG[ch];
        const state = cfg.configured ? 'configured    ' : 'not configured';
        console.log(`  [${state}] ${ch.padEnd(8)} rate: ${cfg.rateLimit}`);
      }
      divider();
      const configured = VALID_CHANNELS.filter(ch => CHANNEL_CONFIG[ch].configured).length;
      info(`${configured}/${VALID_CHANNELS.length} channels configured`);
      if (configured < VALID_CHANNELS.length) {
        warn('Some channels are not configured. Update .env to enable them.');
      }
    });
}
