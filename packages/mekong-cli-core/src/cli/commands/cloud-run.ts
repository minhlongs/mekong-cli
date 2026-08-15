/**
 * cloud-run command — `mekong cloud run "goal"`
 * Full PEV (Plan→Execute→Verify) loop via RaaS Gateway
 */

import type { Command } from 'commander';
import { PEVBridge, PEVTimeoutError } from '../../core/pev-bridge.js';
import { createSpinner } from '../ui/spinner.js';
import { success, error as showError, info, keyValue, divider } from '../ui/output.js';
import type { MissionStatus } from '@mekong/raas-sdk';

const STATUS_ICONS: Record<MissionStatus, string> = {
  pending: '…',
  processing: '⟳',
  completed: '✓',
  failed: '✗',
  cancelled: '⊘',
};

export function registerCloudRunCommand(program: Command): void {
  const cloud = program
    .command('cloud')
    .description('Cloud execution — PEV loop via RaaS Gateway');

  cloud
    .command('run <goal>')
    .description('Run a goal through Plan→Execute→Verify on RaaS Gateway')
    .option('--json', 'Output result as JSON')
    .action(async (goal: string, opts: { json?: boolean }) => {
      const bridge = new PEVBridge();
      const spinner = createSpinner('Connecting to RaaS Gateway...');
      spinner.start();

      bridge.on('plan_start', () => {
        spinner.text = 'Planning mission…';
      });

      bridge.on('plan_done', (missionId: string) => {
        spinner.text = `Mission ${missionId.slice(0, 8)} — executing…`;
      });

      bridge.on('execute_progress', (attempt: number, status: MissionStatus) => {
        const icon = STATUS_ICONS[status] ?? '?';
        spinner.text = `Executing [${icon} ${status}] — poll #${attempt}`;
      });

      bridge.on('verify_result', (passed: boolean, retries: number) => {
        if (!passed && retries < 2) {
          spinner.text = `Verify failed — retrying (${retries + 1}/2)…`;
        }
      });

      try {
        const result = await bridge.run(goal);
        spinner.stop();

        if (opts.json) {
          process.stdout.write(JSON.stringify(result, null, 2) + '\n');
          return;
        }

        const statusIcon = STATUS_ICONS[result.status] ?? '?';
        success(`Mission complete [${statusIcon} ${result.status}]`);
        divider();
        keyValue('Mission ID', result.mission_id);
        keyValue('Status', result.status);
        keyValue('Credits used', `${result.credits_used} MCU`);
        if (result.retries > 0) keyValue('Retries', String(result.retries));

        if (result.outputs) {
          divider();
          info('Output:');
          process.stdout.write(result.outputs + '\n');
        } else if (result.status !== 'completed') {
          showError('No output — mission did not complete successfully.');
          process.exitCode = 1;
        }
      } catch (err) {
        spinner.fail();
        if (err instanceof PEVTimeoutError) {
          showError(err.message);
          info('Check status: mekong mission list');
        } else {
          showError(err instanceof Error ? err.message : String(err));
        }
        process.exitCode = 1;
      }
    });
}
