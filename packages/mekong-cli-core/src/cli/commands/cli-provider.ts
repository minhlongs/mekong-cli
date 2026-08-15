/**
 * cli-provider.ts — CLI provider management commands
 * List, switch, and manage AI CLI providers (claude, gemini, qwen, blackbox).
 */
import type { Command } from 'commander';
import type { MekongEngine } from '../../core/engine.js';
import { success, error as showError, info } from '../ui/output.js';
import { discoverClis } from '@openclaw/cli-adapter';

export function registerCliProviderCommand(program: Command, _engine: MekongEngine): void {
  const cli = program
    .command('cli')
    .description('AI CLI provider management');

  cli
    .command('list')
    .description('List discovered CLI providers and their status')
    .action(async () => {
      try {
        const providers = discoverClis();
        if (providers.length === 0) {
          info('No CLI providers found in PATH');
          return;
        }
        info(`── ${providers.length} CLI Provider(s) ──`);
        for (const p of providers) {
          const status = p.path ? '✅' : '❌';
          info(`  ${status} ${p.name} — ${p.binary}${p.version ? ` (${p.version})` : ''}`);
        }
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });

  cli
    .command('switch <provider>')
    .description('Switch active CLI provider (claude, gemini, qwen, blackbox)')
    .action(async (provider: string) => {
      try {
        const fs = await import('fs');
        const path = await import('path');
        const os = await import('os');

        const configPath = path.join(os.homedir(), '.mekong', 'cli-config.json');
        const configDir = path.dirname(configPath);
        if (!fs.existsSync(configDir)) fs.mkdirSync(configDir, { recursive: true });

        const config = fs.existsSync(configPath)
          ? JSON.parse(fs.readFileSync(configPath, 'utf-8'))
          : {};

        config.activeProvider = provider;
        config.updatedAt = new Date().toISOString();
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

        success(`Active CLI provider switched to: ${provider}`);
      } catch (err) {
        showError(err instanceof Error ? err.message : String(err));
        process.exitCode = 1;
      }
    });
}
