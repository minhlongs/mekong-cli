/**
 * Cloud mission commands — submit, list, get via RaaS gateway
 */
import type { Command } from 'commander';
import { requireCloudClient } from '../../core/raas-client.js';
import { success, error as showError, info } from '../ui/output.js';
import type { Complexity, MissionStatus } from '@mekong/raas-sdk';

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 30;

export function registerCloudMissionCommand(program: Command): void {
  const mission = program
    .command('mission')
    .description('Cloud missions — submit AI tasks via RaaS gateway');

  mission
    .command('submit <goal>')
    .description('Submit a mission (costs MCU credits)')
    .option('-c, --complexity <level>', 'simple|standard|complex', 'simple')
    .option('-w, --wait', 'Wait for result (poll every 2s, up to 60s)')
    .action(async (goal: string, opts: { complexity: string; wait?: boolean }) => {
      try {
        const client = requireCloudClient();
        const mission = await client.missions.submit({
          goal,
          complexity: opts.complexity as Complexity,
        });
        success(`Mission submitted: ${mission.id}`);
        info(`Status: ${mission.status} | Cost: ${mission.credits_cost} MCU`);

        if (opts.wait) {
          info('Waiting for result...');
          for (let i = 0; i < POLL_MAX_ATTEMPTS; i++) {
            await new Promise<void>((r) => setTimeout(r, POLL_INTERVAL_MS));
            const polled = await client.missions.poll(mission.id);
            if (polled.status === 'completed') {
              success('Mission completed!');
              // Fetch full mission for result
              const full = await client.missions.get(mission.id);
              if (full.result) {
                process.stdout.write('\n' + full.result + '\n');
              }
              return;
            }
            if (polled.status === 'failed' || polled.status === 'cancelled') {
              showError(`Mission ${polled.status}`);
              process.exitCode = 1;
              return;
            }
          }
          info(`Still processing. Check: mekong mission get ${mission.id}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  mission
    .command('list')
    .description('List your missions')
    .option('-l, --limit <n>', 'Max results', '10')
    .option('-s, --status <status>', 'Filter by status (pending|processing|completed|failed)')
    .action(async (opts: { limit: string; status?: string }) => {
      try {
        const client = requireCloudClient();
        const response = await client.missions.list({
          limit: parseInt(opts.limit, 10),
          ...(opts.status ? { status: opts.status as MissionStatus } : {}),
        });
        const missions = response.data;
        if (missions.length === 0) {
          info('No missions yet. Try: mekong mission submit "Write a blog post"');
          return;
        }
        info(`Showing ${missions.length} of ${response.total} missions:`);
        for (const m of missions) {
          const icon = m.status === 'completed' ? '✓' : m.status === 'failed' ? '✗' : '…';
          const goal = m.goal.length > 50 ? m.goal.slice(0, 47) + '...' : m.goal;
          info(`${icon} ${m.id.slice(0, 8)} | ${goal} | ${m.credits_cost} MCU | ${m.status}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  mission
    .command('get <id>')
    .description('Get mission details')
    .action(async (id: string) => {
      try {
        const client = requireCloudClient();
        const m = await client.missions.get(id);
        info(`ID:         ${m.id}`);
        info(`Goal:       ${m.goal}`);
        info(`Complexity: ${m.complexity}`);
        info(`Status:     ${m.status}`);
        info(`Cost:       ${m.credits_cost} MCU`);
        info(`Created:    ${m.created_at}`);
        if (m.completed_at) info(`Completed:  ${m.completed_at}`);
        if (m.result) {
          info(`\nResult:\n${m.result}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  mission
    .command('cancel <id>')
    .description('Cancel a pending/processing mission')
    .action(async (id: string) => {
      try {
        const client = requireCloudClient();
        const result = await client.missions.cancel(id);
        if (result.success) {
          success(`Mission cancelled. Refunded: ${result.refunded} MCU`);
        } else {
          showError('Cancel failed');
          process.exitCode = 1;
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
