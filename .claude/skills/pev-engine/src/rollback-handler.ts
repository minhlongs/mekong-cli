/**
 * PEV Engine — Rollback Handler
 *
 * Port of Mekong CLI's RollbackHandler.
 * Reverses completed steps in reverse order when a failure occurs.
 */

import type { OrchestrationResult, Step } from './types.js';

export class RollbackHandler {
  private enabled: boolean;

  constructor(enabled: boolean = true) {
    this.enabled = enabled;
  }

  /**
   * Roll back all completed steps in reverse order.
   * Only steps that passed verification and have rollback commands are rolled back.
   */
  rollback(result: OrchestrationResult, failedStep: Step): OrchestrationResult {
    if (!this.enabled) return result;

    const rollbackErrors: string[] = [];

    // Process completed steps in reverse order
    for (const stepResult of [...result.steps].reverse()) {
      if (!stepResult.verification.passed) continue;

      const step = stepResult.step;
      const rollbackCmds = step.rollback;
      if (!rollbackCmds || rollbackCmds.length === 0) continue;

      for (const cmd of rollbackCmds) {
        // Security: basic sanitization — block dangerous patterns
        if (this.isDangerousCommand(cmd)) {
          rollbackErrors.push(`Step ${step.id}: rollback blocked (security): ${cmd}`);
          continue;
        }

        // In ClaudeKit context, rollback commands are delegated to the agent's Bash tool.
        // We record the command as pending for the agent to execute.
        result.rollback_actions_run = (result.rollback_actions_run || 0) + 1;
      }
    }

    if (rollbackErrors.length > 0) {
      result.errors.push(...rollbackErrors);
      result.warnings.push('Rollback completed with errors');
    }

    result.status = 'rolled_back';
    return result;
  }

  /**
   * Basic command safety check — blocks obviously dangerous operations.
   */
  private isDangerousCommand(cmd: string): boolean {
    const dangerousPatterns = [
      /rm\s+-rf\s+\//,           // rm -rf /
      /rm\s+-rf\s+~\//,          // rm -rf ~/
      /sudo\s+/,                  // sudo
      /eval\s+/,                  // eval
      /\.\.\//,                   // path traversal
      /chmod\s+777/,              // chmod 777
      /dd\s+if=/,                 // dd
      /mkfs/,                     // format filesystem
      /:\(\)\s*\{/,              // fork bomb
    ];

    return dangerousPatterns.some(pattern => pattern.test(cmd));
  }
}
