/**
 * cto.ts — CTO brain management CLI commands
 * Status, dispatch, reset for the Auto-CTO orchestration engine.
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';

export function registerCtoCommand(program: Command, _engine: MekongEngine): void {
  const cto = program
    .command('cto-brain')
    .description('CTO brain management — status, dispatch, reset');

  cto
    .command('status')
    .description('Show CTO brain state, project priority, pane health')
    .action(async () => {
      try {
        const { getCtoStatus } = await import('../../../../openclaw-engine/src/orchestration/auto-cto-pilot.js');
        const status = getCtoStatus();
        info('── CTO Brain Status ──');
        info(`Phase: ${status.phase}`);
        info(`Project index: ${status.currentProjectIdx}`);
        info(`Cycle: ${status.cycle}`);
        info(`Errors: ${status.errorCount} (fix index: ${status.fixIndex})`);
        info(`Panes: ${status.totalPanes} active`);
        info(`Cooldown: ${status.cooldownMs / 1000}s per pane`);
        info('── Project Priority ──');
        const sorted = Object.entries(status.priorities)
          .sort(([, a], [, b]) => (a as number) - (b as number));
        for (const [name, priority] of sorted) {
          info(`  ${priority}. ${name}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  cto
    .command('dispatch <task> [pane]')
    .description('Manual task injection to a specific pane')
    .action(async (task: string, pane?: string) => {
      try {
        const fs = await import('fs');
        const path = await import('path');
        const os = await import('os');

        const watchDir = path.join(os.homedir(), '.mekong', 'tasks');
        if (!fs.existsSync(watchDir)) {
          fs.mkdirSync(watchDir, { recursive: true });
        }

        const panePrefix = pane ? `P${pane}_` : '';
        const filename = `${panePrefix}MANUAL_${Date.now()}.md`;
        const taskPath = path.join(watchDir, filename);
        fs.writeFileSync(taskPath, task);
        success(`Task queued: ${filename}`);
        info(`Path: ${taskPath}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  cto
    .command('reset')
    .description('Reset CTO state machine to clean scan phase')
    .action(async () => {
      try {
        const { resetCtoState } = await import('../../../../openclaw-engine/src/orchestration/auto-cto-pilot.js');
        const state = resetCtoState();
        success('CTO state reset to clean state');
        info(`Phase: ${state.phase}, project: ${state.currentProjectIdx}, cycle: ${state.cycle}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
