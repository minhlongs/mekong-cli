/**
 * Mekong Persona - Mekong CLI command set and behavior
 */

import { Harness } from '../core/harness';

export class MekongPersona {
  name = 'mekong';
  description = 'Mekong CLI - The One-Person Unicorn Operating System';

  applyToHarness(harness: Harness): void {
    // Override model for heavy commands
    harness.llmRouter.defaultModel = 'claude-opus-4-8';
    
    // Add Mekong-specific command aliases
    console.log('[MekongPersona] Applied Mekong persona configuration');
  }

  getCommands() {
    return [
      'strategy:analyze',
      'strategy:plan', 
      'strategy:win3',
      'finance:autopilot',
      'finance:report',
      'particle:run',
      'studio:launch',
      'outreach:campaign',
      'sales:pipeline',
      'content:generate',
      'ops:deploy',
      'setup:wizard',
      'bridge:sync',
      'workflow:run',
      'palette:open',
      'dashboard',
      'activate',
      'status',
      'setup-vibe',
      'cook',
      'test',
      'ship',
      'scaffold',
      'tui',
      'agents',
    ];
  }

  getModelForCommand(command: string): string {
    // Heavy commands use Opus
    const heavyCommands = ['cook', 'fix', 'plan', 'strategy:plan', 'strategy:analyze', 'code', 'review'];
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
║   🌊 MEKONG-CLI & 🏯 AGENCY OS                            ║
║                                                           ║
║   The One-Person Unicorn Operating System                ║
║   "Không đánh mà thắng" - Win Without Fighting           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝[/bold primary]
`;
  }
}
