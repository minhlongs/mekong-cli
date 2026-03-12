import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { heading, keyValue, divider } from '../ui/output.js';

export function registerStatusCommand(program: Command, engine: MekongEngine): void {
  program
    .command('status')
    .description('Show engine status')
    .action(() => {
      const status = engine.getStatus();
      heading('Mekong Engine Status');
      keyValue('Initialized', String(status.initialized));
      keyValue('Providers', status.providers.join(', ') || 'none');
      keyValue('Tools', String(status.toolCount));
      keyValue('Session', status.sessionId ?? 'none');
      divider();
    });
}
