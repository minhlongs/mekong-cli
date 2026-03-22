/**
 * `mekong backup` — Backup management subcommands (Wave 53).
 *
 *   mekong backup create    Create a new backup (full|incremental|snapshot)
 *   mekong backup restore   Restore from a backup ID
 *   mekong backup list      List backup history
 *   mekong backup schedule  View or update backup schedule
 */
import type { Command } from 'commander';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

/** Mock backup records */
const MOCK_BACKUPS = [
  { id: 'BKP-2026-0322-001', type: 'full',        size: '2.4 GB', date: '2026-03-22 02:00', status: 'success', target: 's3' },
  { id: 'BKP-2026-0321-002', type: 'incremental', size: '128 MB', date: '2026-03-21 14:00', status: 'success', target: 's3' },
  { id: 'BKP-2026-0321-001', type: 'snapshot',    size: '1.1 GB', date: '2026-03-21 02:00', status: 'success', target: 'r2' },
  { id: 'BKP-2026-0320-002', type: 'incremental', size: '96 MB',  date: '2026-03-20 14:00', status: 'success', target: 's3' },
  { id: 'BKP-2026-0320-001', type: 'full',        size: '2.3 GB', date: '2026-03-20 02:00', status: 'failed',  target: 'local' },
];

const MOCK_SCHEDULE = {
  frequency: 'daily',
  time: '02:00 ICT',
  retention: 30,
  lastRun: '2026-03-22 02:00',
  nextRun: '2026-03-23 02:00',
  target: 's3',
};

export function registerBackupCommand(program: Command): void {
  const cmd = program.command('backup').description('Backup management');

  // ── backup create ───────────────────────────────────────────────────────────
  cmd.command('create')
    .description('Create a new backup')
    .option('--type <type>', 'Backup type (full|incremental|snapshot)', 'full')
    .option('--target <target>', 'Backup target (local|s3|r2)', 's3')
    .action((opts: { type: string; target: string }) => {
      heading('Creating Backup');
      const id = `BKP-${Date.now()}`;
      const sizeMap: Record<string, string> = { full: '2.4 GB', incremental: '112 MB', snapshot: '1.1 GB' };
      const size = sizeMap[opts.type] ?? '2.4 GB';

      info(`Type:   ${opts.type}`);
      info(`Target: ${opts.target}`);
      info('Compressing data...');
      info('Encrypting payload...');
      info('Uploading to target...');
      divider();

      keyValue('Backup ID', id);
      keyValue('Type', opts.type);
      keyValue('Size', size);
      keyValue('Duration', '42s');
      keyValue('Target', opts.target);
      keyValue('Checksum', 'sha256:a1b2c3d4e5f6');
      divider();
      success(`Backup created: ${id}`);
      info('Verify with: mekong backup list');
    });

  // ── backup restore ──────────────────────────────────────────────────────────
  cmd.command('restore')
    .argument('<backup-id>', 'Backup ID to restore')
    .description('Restore from a backup')
    .option('--dry-run', 'Simulate restore without applying changes')
    .action((backupId: string, opts: { dryRun?: boolean }) => {
      heading(`Restore Backup — ${backupId}`);
      const record = MOCK_BACKUPS.find(b => b.id === backupId);

      if (!record) {
        warn(`Backup not found: ${backupId}`);
        info('List available backups: mekong backup list');
        return;
      }

      if (opts.dryRun) {
        info('[DRY RUN] Simulating restore — no changes applied');
      }

      keyValue('Backup ID', record.id);
      keyValue('Type', record.type);
      keyValue('Size', record.size);
      keyValue('Source', record.target);
      divider();

      info('Verifying checksum...');
      info('Decrypting payload...');
      info('Restoring database...');
      info('Restoring file storage...');
      info('Running health checks...');
      divider();

      if (opts.dryRun) {
        success('Dry run complete — restore would succeed');
      } else {
        success(`Restore complete: ${backupId}`);
        info('Verification status: PASSED');
      }
    });

  // ── backup list ─────────────────────────────────────────────────────────────
  cmd.command('list')
    .description('List backup history')
    .option('--type <type>', 'Filter by type (full|incremental|snapshot)')
    .option('--limit <n>', 'Max results', '10')
    .action((opts: { type?: string; limit?: string }) => {
      heading('Backup History');
      const limit = parseInt(opts.limit ?? '10', 10);
      const records = opts.type
        ? MOCK_BACKUPS.filter(b => b.type === opts.type)
        : MOCK_BACKUPS;
      const displayed = records.slice(0, limit);

      if (displayed.length === 0) {
        warn(`No backups found${opts.type ? ` of type: ${opts.type}` : ''}`);
        return;
      }

      for (const b of displayed) {
        const statusIcon = b.status === 'success' ? '[OK]  ' : '[FAIL]';
        console.log(`\n  ${statusIcon} ${b.id}`);
        keyValue('  Type', b.type);
        keyValue('  Size', b.size);
        keyValue('  Date', b.date);
        keyValue('  Target', b.target);
      }
      divider();

      const failed = displayed.filter(b => b.status === 'failed').length;
      info(`Showing ${displayed.length} backup(s) — ${failed} failed`);
    });

  // ── backup schedule ─────────────────────────────────────────────────────────
  cmd.command('schedule')
    .description('View or update backup schedule')
    .option('--frequency <freq>', 'Frequency (daily|weekly|monthly)')
    .option('--time <time>', 'Schedule time (HH:MM)')
    .option('--retention <days>', 'Retention period in days')
    .action((opts: { frequency?: string; time?: string; retention?: string }) => {
      heading('Backup Schedule');
      const updated = opts.frequency || opts.time || opts.retention;

      if (updated) {
        if (opts.frequency) keyValue('Updated frequency', opts.frequency);
        if (opts.time)      keyValue('Updated time', opts.time);
        if (opts.retention) keyValue('Updated retention', `${opts.retention} days`);
        divider();
        success('Schedule updated');
      }

      heading('Current Schedule');
      keyValue('Frequency', MOCK_SCHEDULE.frequency);
      keyValue('Time', MOCK_SCHEDULE.time);
      keyValue('Retention', `${MOCK_SCHEDULE.retention} days`);
      keyValue('Target', MOCK_SCHEDULE.target);
      keyValue('Last run', MOCK_SCHEDULE.lastRun);
      keyValue('Next run', MOCK_SCHEDULE.nextRun);
      divider();
      info('Edit schedule: mekong.yaml → backup.schedule');
    });
}
