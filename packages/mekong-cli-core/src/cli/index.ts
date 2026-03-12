#!/usr/bin/env node
import { Command } from 'commander';
import { MekongEngine } from '../core/engine.js';
import { registerRunCommand } from './commands/run.js';
import { registerSopCommand } from './commands/sop.js';
import { registerStatusCommand } from './commands/status.js';

const VERSION = '0.1.0';

export async function main(argv?: string[]): Promise<void> {
  const program = new Command();
  const engine = new MekongEngine();

  program
    .name('mekong')
    .description('AI-operated business platform CLI')
    .version(VERSION);

  // Init engine before any command action runs
  program.hook('preAction', async () => {
    try {
      await engine.init({
        askUser: async (q) => {
          process.stdout.write(q + ' ');
          return new Promise((resolve) => {
            process.stdin.once('data', (data) => resolve(data.toString().trim()));
          });
        },
      });
    } catch {
      // Engine init may fail when no LLM configured — status cmd still works
    }
  });

  registerRunCommand(program, engine);
  registerSopCommand(program, engine);
  registerStatusCommand(program, engine);

  await program.parseAsync(argv ?? process.argv);
}

// Auto-run when executed directly
const isDirectRun = process.argv[1]?.includes('mekong') || process.argv[1]?.includes('index');
if (isDirectRun) {
  main().catch(console.error);
}
