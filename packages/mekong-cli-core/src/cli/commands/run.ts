import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError } from '../ui/output.js';
import { withSpinner } from '../ui/spinner.js';

export function registerRunCommand(program: Command, engine: MekongEngine): void {
  program
    .command('run <task...>')
    .description('Run a natural language task')
    .option('-v, --verbose', 'Show detailed output')
    .action(async (taskParts: string[], _opts: { verbose?: boolean }) => {
      const task = taskParts.join(' ');
      try {
        const result = await withSpinner(`Running: ${task}`, () => engine.run(task));
        success('Task completed');
        console.log(result);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
