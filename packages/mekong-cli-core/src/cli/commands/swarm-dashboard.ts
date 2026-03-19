/**
 * swarm-dashboard.ts — AgencyOS Dashboard + Swarm CLI commands
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerSwarmDashboardCommand(program: Command, _engine: MekongEngine): void {
  const dash = program
    .command('live-dashboard')
    .description('AgencyOS live dashboard — system overview');

  dash
    .command('show')
    .description('Show full terminal dashboard')
    .action(async () => {
      try {
        // @ts-expect-error rootDir constraint
        const { DashboardApi } = await import('../../../agencyos-dashboard/src/api.js');
        // @ts-expect-error rootDir constraint
        const { TerminalDashboard } = await import('../../../agencyos-dashboard/src/renderer.js');
        const api = new DashboardApi();
        const renderer = new TerminalDashboard();
        const status = api.handleRequest('GET', '/status');
        const panes = api.handleRequest('GET', '/panes');
        const tasks = api.handleRequest('GET', '/tasks');
        const output = renderer.renderFullDashboard({
          status: status.body as any,
          panes: (panes.body as any).panes ?? [],
          tasks: (tasks.body as any).tasks ?? [],
          raas: { tenants: 0, revenue: 0, health: 'unknown' },
          agiScore: { score: 0, capabilitiesCount: 0 },
        });
        info(output);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  dash
    .command('compact')
    .description('Show compact single-line status')
    .action(async () => {
      try {
        // @ts-expect-error rootDir constraint
        const { TerminalDashboard } = await import('../../../agencyos-dashboard/src/renderer.js');
        const renderer = new TerminalDashboard();
        info(renderer.renderCompactView({
          status: { uptime: process.uptime() * 1000, version: '0.1.0', paneCount: 4, taskCount: 0 },
          panes: [], tasks: [], raas: { tenants: 0, revenue: 0, health: 'unknown' }, agiScore: { score: 0, capabilitiesCount: 0 },
        }));
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  // Swarm commands
  const swarm = program
    .command('swarm')
    .description('Multi-CLI swarm orchestration');

  swarm
    .command('start')
    .description('Start CLI swarm with available providers')
    .action(async () => {
      try {
        // @ts-expect-error rootDir constraint
        const { CliSwarm } = await import('../../../cli-orchestrator/src/swarm.js');
        const sw = new CliSwarm();
        sw.addProvider('claude', 1);
        sw.addProvider('gemini', 2);
        sw.addProvider('qwen', 3);
        const balance = sw.getLoadBalance();
        success('Swarm initialized');
        info(`Providers: ${balance.map((p: any) => p.provider).join(', ')}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  swarm
    .command('status')
    .description('Show swarm load balance')
    .action(async () => {
      try {
        // @ts-expect-error rootDir constraint
        const { CliSwarm } = await import('../../../cli-orchestrator/src/swarm.js');
        const sw = new CliSwarm();
        const balance = sw.getLoadBalance();
        info('── Swarm Status ──');
        for (const p of balance) {
          info(`  ${p.provider}: ${p.activeTasks} active, ${p.totalCompleted} completed`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
