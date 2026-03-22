import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { heading, keyValue, divider, success, info, warn } from '../ui/output.js';

export function registerStatusCommand(program: Command, engine: MekongEngine): void {
  program
    .command('status')
    .description('Show engine status with OpenClaw health metrics')
    .option('--json', 'Output as JSON')
    .action((opts: { json?: boolean }) => {
      const status = engine.getStatus();

      if (opts.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }

      heading('Mekong Engine Status');
      keyValue('Initialized', String(status.initialized));
      keyValue('Providers', status.providers.join(', ') || 'none');
      keyValue('Tools', String(status.toolCount));
      keyValue('Session', status.sessionId ?? 'none');
      keyValue('License Tier', status.tier);
      divider();

      if (status.openclaw) {
        heading('OpenClaw Engine Health');
        keyValue('Missions Completed', String(status.openclaw.missionsCompleted));
        keyValue('AGI Score', `${status.openclaw.agiScore}/100`);

        const cb = status.openclaw.circuitBreaker;
        if (cb === 'closed') success(`Circuit Breaker: ${cb} (healthy)`);
        else if (cb === 'half-open') warn(`Circuit Breaker: ${cb} (recovering)`);
        else warn(`Circuit Breaker: ${cb} (tripped)`);

        const uptimeSec = Math.round(status.openclaw.uptime / 1000);
        const uptimeMin = Math.round(uptimeSec / 60);
        keyValue('Uptime', uptimeMin > 0 ? `${uptimeMin}m` : `${uptimeSec}s`);
        divider();
      }

      if (status.usage) {
        heading('LLM Usage');
        const tokens = (status.usage.totalInputTokens ?? 0) + (status.usage.totalOutputTokens ?? 0);
        keyValue('Total tokens', String(tokens));
        keyValue('Total cost', `$${(status.usage.totalCost ?? 0).toFixed(4)}`);
        divider();
      }

      info('');
      info('Commands: mekong analytics roi | mekong demo pitch | mekong onboard check');
      info('');
    });
}
