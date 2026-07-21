/**
 * Hook Engine - Unified hook system for both personas
 * Loads hooks from .claude/settings.json and executes them
 */

import { Hook, HookEvent, HookContext, HookResult, HarnessConfig, Persona } from './types';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

export class HookEngine {
  private hooks: Hook[] = [];
  private config: HarnessConfig;

  constructor(config: HarnessConfig) {
    this.config = config;
    this.loadHooks();
  }

  private loadHooks(): void {
    // Load hooks from config (already parsed by ConfigManager)
    this.hooks = [...(this.config.hooks || [])];

    // Also load from local .claude/hooks/ directory if exists
    const localHooksDir = path.join(this.config.configRoot, '.claude', 'hooks');
    if (fs.existsSync(localHooksDir)) {
      const files = fs.readdirSync(localHooksDir).filter(f => f.endsWith('.cjs') || f.endsWith('.js'));
      for (const file of files) {
        const hookPath = path.join(localHooksDir, file);
        try {
          const hookDef = this.parseHookFile(hookPath);
          if (hookDef) {
            this.hooks.push(hookDef);
          }
        } catch {
          // Skip invalid hooks
        }
      }
    }
  }

  private parseHookFile(filePath: string): Hook | null {
    // For .cjs files, we can't easily extract metadata without executing
    // Instead, we rely on settings.json for hook registration
    return null;
  }

  async fire(event: HookEvent, context: HookContext): Promise<HookResult> {
    const relevantHooks = this.hooks.filter(hook => {
      if (hook.event !== event && hook.event !== 'all') return false;
      if (hook.persona && hook.persona !== 'both' && hook.persona !== context.persona) return false;
      return this.matchTool(hook.matcher, context.toolName || '');
    });

    let finalResult: HookResult = { allowed: true };

    for (const hook of relevantHooks) {
      const result = await this.executeHook(hook, context);
      if (!result.allowed) {
        return result; // First denial wins
      }
      if (result.output) {
        finalResult.output = (finalResult.output || '') + result.output;
      }
      if (result.modifiedInput) {
        finalResult.modifiedInput = result.modifiedInput;
      }
    }

    return finalResult;
  }

  private matchTool(matcher: string, toolName: string): boolean {
    if (matcher === '*' || matcher === 'all') return true;
    const patterns = matcher.split('|').map(p => p.trim());
    return patterns.some(p => {
      if (p === toolName) return true;
      if (p.endsWith('*')) return toolName.startsWith(p.slice(0, -1));
      return false;
    });
  }

  private async executeHook(hook: Hook, context: HookContext): Promise<HookResult> {
    return new Promise((resolve) => {
      const timeout = hook.timeout || 30000;
      let timedOut = false;

      const timer = setTimeout(() => {
        timedOut = true;
        resolve({
          allowed: true, // Fail-open on timeout
          error: `Hook timeout after ${timeout}ms`,
        });
      }, timeout);

      const proc = spawn(hook.command, {
        shell: true,
        cwd: context.cwd,
        env: {
          ...context.env,
          CLAUDE_HOOK_EVENT: context.event,
          CLAUDE_HOOK_TOOL_NAME: context.toolName || '',
          CLAUDE_HOOK_SESSION_ID: context.sessionId,
          CLAUDE_HOOK_PERSONA: context.persona,
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      // Write tool input to stdin
      if (context.toolInput) {
        proc.stdin?.write(JSON.stringify(context.toolInput));
        proc.stdin?.end();
      }

      proc.stdout?.on('data', (data) => { stdout += data.toString(); });
      proc.stderr?.on('data', (data) => { stderr += data.toString(); });

      proc.on('close', (code) => {
        clearTimeout(timer);
        if (timedOut) return;

        try {
          // Try to parse JSON output for structured result
          const output = stdout.trim();
          if (output.startsWith('{')) {
            const result = JSON.parse(output);
            resolve({
              allowed: result.allowed ?? true,
              output: result.output,
              error: result.error,
              modifiedInput: result.modifiedInput,
            });
          } else {
            // Non-zero exit = block
            resolve({
              allowed: code === 0,
              output: output || stderr,
              error: code !== 0 ? stderr : undefined,
            });
          }
        } catch {
          resolve({
            allowed: code === 0,
            output: stdout,
            error: stderr || (code !== 0 ? `Exit code ${code}` : undefined),
          });
        }
      });

      proc.on('error', (err) => {
        clearTimeout(timer);
        if (timedOut) return;
        // Fail-open
        resolve({ allowed: true, error: `Hook execution error: ${err.message}` });
      });
    });
  }

  getHooks(): Hook[] {
    return [...this.hooks];
  }

  getHooksForEvent(event: HookEvent, persona: Persona): Hook[] {
    return this.hooks.filter(h => {
      if (h.event !== event && h.event !== 'all') return false;
      if (h.persona && h.persona !== 'both' && h.persona !== persona) return false;
      return true;
    });
  }
}