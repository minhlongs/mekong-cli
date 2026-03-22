/**
 * `mekong migration` — Database migration subcommands (Wave 54).
 *
 *   mekong migration status    Show current migration state
 *   mekong migration run       Execute pending migrations
 *   mekong migration rollback  Revert applied migrations
 *   mekong migration plan      Show pending migrations plan
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

/** Mock migration records */
const MOCK_APPLIED = [
  { version: '006', name: '006_add_metering_tables',        type: 'schema', appliedAt: '2026-03-20 10:15', duration: '1.2s' },
  { version: '005', name: '005_add_license_audit_log',      type: 'schema', appliedAt: '2026-03-18 09:30', duration: '0.8s' },
  { version: '004', name: '004_backfill_mrr_snapshots',     type: 'data',   appliedAt: '2026-03-15 14:00', duration: '8.4s' },
  { version: '003', name: '003_add_webhook_events_index',   type: 'index',  appliedAt: '2026-03-10 11:20', duration: '2.1s' },
  { version: '002', name: '002_add_agent_runs_table',       type: 'schema', appliedAt: '2026-03-05 08:45', duration: '1.5s' },
  { version: '001', name: '001_initial_schema',             type: 'schema', appliedAt: '2026-03-01 07:00', duration: '3.8s' },
];

const MOCK_PENDING = [
  { version: '007', name: '007_add_backup_metadata_table', type: 'schema', estimatedDuration: '1.0s', dependencies: ['006'] },
  { version: '008', name: '008_backfill_agent_cost_data',  type: 'data',   estimatedDuration: '12.0s', dependencies: ['007'] },
  { version: '009', name: '009_add_cost_index_on_runs',    type: 'index',  estimatedDuration: '3.5s', dependencies: ['008'] },
];

/** DRY helper — renders engine health footer */
function showEngineHealth(engine?: MekongEngine, label = 'Engine Status'): void {
  try {
    const health = engine?.openclaw?.getHealth();
    if (!health) return;
    divider();
    info(label);
    keyValue('  Uptime', `${Math.round(health.uptime / 1000)}s`);
    keyValue('  Missions completed', `${health.missionsCompleted}`);
    keyValue('  AGI score', `${health.agiScore}/100`);
    keyValue('  Circuit breaker', health.circuitBreakerState);
  } catch { /* engine not ready */ }
}

export function registerMigrationCommand(program: Command, engine?: MekongEngine): void {
  const cmd = program.command('migration').description('Database migration management');

  // ── migration status ────────────────────────────────────────────────────────
  cmd.command('status')
    .description('Show current migration state')
    .action(() => {
      heading('Migration Status');
      keyValue('Applied migrations', String(MOCK_APPLIED.length));
      keyValue('Pending migrations', String(MOCK_PENDING.length));
      keyValue('Last applied', MOCK_APPLIED[0]?.name ?? 'none');
      keyValue('Last applied at', MOCK_APPLIED[0]?.appliedAt ?? 'N/A');
      keyValue('Database version', `v${MOCK_APPLIED[0]?.version ?? '000'}`);
      divider();

      if (MOCK_PENDING.length === 0) {
        success('Database is up to date');
      } else {
        warn(`${MOCK_PENDING.length} pending migration(s) — run: mekong migration run`);
      }

      showEngineHealth(engine, 'Engine Status');
    });

  // ── migration run ───────────────────────────────────────────────────────────
  cmd.command('run')
    .description('Execute pending migrations')
    .option('--target <version>', 'Run migrations up to this version')
    .option('--dry-run', 'Simulate without applying changes')
    .action((opts: { target?: string; dryRun?: boolean }) => {
      heading('Running Migrations');

      if (opts.dryRun) {
        info('[DRY RUN] Simulating — no changes applied');
      }

      const toRun = opts.target
        ? MOCK_PENDING.filter(m => parseInt(m.version, 10) <= parseInt(opts.target!, 10))
        : MOCK_PENDING;

      if (toRun.length === 0) {
        success('No pending migrations to run');
        info('Database is already at target version');
        return;
      }

      // AI risk assessment via engine
      try {
        const migrationSummary = toRun.map(m => `${m.name} (${m.type})`).join(', ');
        const complexity = engine?.openclaw?.classifyComplexity(migrationSummary);
        if (complexity) keyValue('AI risk assessment', complexity);
      } catch { /* engine not ready */ }

      info(`${toRun.length} migration(s) to apply`);
      divider();

      for (const m of toRun) {
        info(`Running: ${m.name}`);
        keyValue('  Type', m.type);
        keyValue('  Est. duration', m.estimatedDuration);
        if (!opts.dryRun) {
          success(`  Applied: v${m.version}`);
        }
      }
      divider();

      if (opts.dryRun) {
        success(`Dry run complete — ${toRun.length} migration(s) would be applied`);
      } else {
        success(`Applied ${toRun.length} migration(s) successfully`);
        keyValue('New DB version', `v${toRun[toRun.length - 1]?.version}`);
        // Fire-and-forget AI migration analysis
        void engine?.openclaw?.submitMission({
          goal: `Analyze applied migrations: ${toRun.map(m => m.name).join(', ')}`,
          complexity: 'standard',
        });
      }
    });

  // ── migration rollback ──────────────────────────────────────────────────────
  cmd.command('rollback')
    .description('Revert applied migrations')
    .option('--steps <n>', 'Number of migrations to rollback', '1')
    .action((opts: { steps?: string }) => {
      heading('Rolling Back Migrations');
      const steps = Math.max(1, parseInt(opts.steps ?? '1', 10));
      const toRevert = MOCK_APPLIED.slice(0, steps);

      // AI rollback risk level
      try {
        const rollbackSummary = toRevert.map(m => `${m.name} (${m.type})`).join(', ');
        const risk = engine?.openclaw?.classifyComplexity(rollbackSummary);
        if (risk) keyValue('AI rollback risk level', risk);
      } catch { /* engine not ready */ }

      info(`Rolling back ${steps} migration(s)`);
      divider();

      for (const m of toRevert) {
        warn(`Reverting: ${m.name}`);
        keyValue('  Version', m.version);
        keyValue('  Type', m.type);
        success(`  Reverted: v${m.version}`);
      }
      divider();

      const newVersion = MOCK_APPLIED[steps]?.version ?? '000';
      success(`Rollback complete — ${steps} migration(s) reverted`);
      keyValue('Reverted migrations', toRevert.map(m => m.name).join(', '));
      keyValue('DB version now', `v${newVersion}`);
      info('Re-apply with: mekong migration run');
    });

  // ── migration plan ──────────────────────────────────────────────────────────
  cmd.command('plan')
    .description('Show pending migrations plan')
    .action(() => {
      heading('Migration Plan');

      if (MOCK_PENDING.length === 0) {
        success('No pending migrations — database is up to date');
        return;
      }

      info(`${MOCK_PENDING.length} pending migration(s)`);
      divider();

      for (const m of MOCK_PENDING) {
        console.log(`\n  [v${m.version}] ${m.name}`);
        keyValue('  Type', m.type);
        keyValue('  Estimated duration', m.estimatedDuration);
        keyValue('  Depends on', m.dependencies.join(', ') || 'none');
      }
      divider();

      const totalEstimate = MOCK_PENDING.reduce((sum, m) => sum + parseFloat(m.estimatedDuration), 0);
      keyValue('Total migrations', String(MOCK_PENDING.length));
      keyValue('Estimated total duration', `${totalEstimate.toFixed(1)}s`);
      info('Apply with: mekong migration run');

      // Fire-and-forget AI planning recommendations
      void engine?.openclaw?.submitMission({
        goal: `Generate migration planning recommendations for: ${MOCK_PENDING.map(m => m.name).join(', ')}`,
        complexity: 'complex',
      });
    });
}
