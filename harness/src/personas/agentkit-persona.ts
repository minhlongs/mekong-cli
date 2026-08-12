/**
 * Agent Kit Persona - Agent Kit / Claude Code command set and behavior
 */

import { Harness } from '../core/harness';

export class AgentKitPersona {
  name = 'agentkit';
  description = 'Agent Kit - Agent Kit on Mekong Harness';

  applyToHarness(harness: Harness): void {
    // Use Fable for most commands, Opus for heavy
    harness.llmRouter.defaultModel = 'claude-fable-5';
    console.log('[AgentKitPersona] Applied Agent Kit persona configuration');
  }

  getCommands() {
    return [
      'plan',
      'cook',
      'fix',
      'review',
      'scout',
      'brainstorm',
      'code',
      'test',
      'ship',
      'docs',
      'simplify',
      'preview',
      'design',
      'deploy',
      'retro',
      'orchestrator',
      'suntzu',
      'kongming',
    ];
  }

  getModelForCommand(command: string): string {
    // Heavy commands use Opus
    const heavyCommands = ['cook', 'fix', 'plan', 'code', 'review'];
    if (heavyCommands.some(c => command.startsWith(c))) {
      return 'claude-opus-4-8';
    }
    // Light commands use Fable
    return 'claude-fable-5';
  }

  getWelcomeBanner(): string {
    return `
[bold primary]╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🏯 AGENT KIT on MEKONG HARNESS                          ║
║                                                           ║
║   Agent Kit Persona - Shared Infrastructure              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝[/bold primary]
`;
  }
}
