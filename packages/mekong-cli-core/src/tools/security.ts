import type { SecurityLevel } from '../types/tool.js';

/**
 * Jidoka-inspired 4-level permission system:
 * Level 0 (Safe):      Auto-approved — file_read, search, http_get
 * Level 1 (Moderate):  Auto-approved + logged — file_write, git_commit
 * Level 2 (Sensitive): Ask first time, remember — http_post, send_message
 * Level 3 (Critical):  ALWAYS ask — deploy, delete, sudo
 */
export class SecurityManager {
  private approvals: Map<string, boolean> = new Map();
  private autoApproveLevel: SecurityLevel;
  private askUser: (question: string) => Promise<boolean>;

  constructor(
    autoApproveLevel: SecurityLevel = 1,
    askUser?: (q: string) => Promise<boolean>,
  ) {
    this.autoApproveLevel = autoApproveLevel;
    this.askUser = askUser ?? (async () => false);
  }

  async checkPermission(
    toolName: string,
    level: SecurityLevel,
    context: string,
  ): Promise<{ allowed: boolean; reason?: string }> {
    // Level 0: always allow
    if (level === 0) return { allowed: true };

    // Level 1: allow if auto-approve >= 1
    if (level === 1 && this.autoApproveLevel >= 1) return { allowed: true };

    // Level 1 denied
    if (level === 1) return { allowed: false, reason: 'Requires manual approval (level 1)' };

    // Level 2: check cache, ask if first time
    if (level === 2) {
      const key = `${toolName}:${context}`;
      if (this.approvals.has(key)) return { allowed: this.approvals.get(key)! };
      if (this.autoApproveLevel >= 2) return { allowed: true };
      const approved = await this.askUser(`Allow "${toolName}" for: ${context}?`);
      this.approvals.set(key, approved);
      return { allowed: approved, reason: approved ? undefined : 'User denied' };
    }

    // Level 3: always ask
    if (level === 3) {
      const approved = await this.askUser(`[CRITICAL] Allow "${toolName}" for: ${context}?`);
      return { allowed: approved, reason: approved ? undefined : 'User denied critical action' };
    }

    return { allowed: false, reason: 'Unknown security level' };
  }

  /** Grant approval for a tool+context (level 2 cache) */
  grant(toolName: string, context: string): void {
    this.approvals.set(`${toolName}:${context}`, true);
  }

  /** Revoke approval for a tool+context */
  revoke(toolName: string, context: string): void {
    this.approvals.delete(`${toolName}:${context}`);
  }

  /** Replace the ask function (for CLI integration) */
  setAskUser(fn: (q: string) => Promise<boolean>): void {
    this.askUser = fn;
  }
}
