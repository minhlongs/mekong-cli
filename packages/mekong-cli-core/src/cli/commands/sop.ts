import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, keyValue } from '../ui/output.js';
import { withSpinner } from '../ui/spinner.js';
import { collectMetrics } from '../../sops/metrics.js';

export function registerSopCommand(program: Command, engine: MekongEngine): void {
  program
    .command('sop <file>')
    .description('Run a SOP definition file')
    .option('-i, --input <key=value...>', 'Provide inputs as key=value pairs')
    .action(async (file: string, opts: { input?: string[] }) => {
      const inputs: Record<string, string> = {};
      if (opts.input) {
        for (const kv of opts.input) {
          const [k, ...v] = kv.split('=');
          inputs[k] = v.join('=');
        }
      }
      try {
        const run = await withSpinner(`Running SOP: ${file}`, () => engine.runSop(file, inputs));
        const metrics = collectMetrics(run);
        if (run.status === 'success') {
          success(`SOP "${run.sopName}" completed`);
        } else {
          showError(`SOP "${run.sopName}" failed: ${run.error ?? 'unknown error'}`);
        }
        keyValue('Duration', `${metrics.totalDurationMs}ms`);
        keyValue('Steps', `${metrics.successCount}/${metrics.stepCount} passed`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
