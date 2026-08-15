import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import type { ToolDefinition, ToolResult } from '../../types/tool.js';

const execAsync = promisify(exec);

const DEFAULT_BLOCKED = ['rm -rf /', 'sudo', 'mkfs', ':(){ :|:& };:', 'dd if=/dev'];

export function createShellTool(options?: {
  blockedCommands?: string[];
  timeoutMs?: number;
  cwd?: string;
}): ToolDefinition {
  const blocked = options?.blockedCommands ?? DEFAULT_BLOCKED;
  const timeout = options?.timeoutMs ?? 30000;

  return {
    name: 'shell',
    description: 'Execute a shell command in a sandboxed environment',
    category: 'shell',
    securityLevel: 1,
    params: [
      { name: 'command', type: 'string', description: 'Shell command to execute', required: true },
    ],
    execute: async (params): Promise<ToolResult> => {
      const command = params.command as string;
      const startTime = Date.now();

      for (const pattern of blocked) {
        if (command.includes(pattern)) {
          return { success: false, output: '', error: `Blocked command pattern: ${pattern}` };
        }
      }

      try {
        const { stdout, stderr } = await execAsync(command, {
          timeout,
          cwd: options?.cwd,
          maxBuffer: 1024 * 1024 * 5,
        });
        return {
          success: true,
          output: stdout + (stderr ? `\n[stderr] ${stderr}` : ''),
          metadata: { durationMs: Date.now() - startTime },
        };
      } catch (error: unknown) {
        const err = error as { stdout?: string; stderr?: string; message?: string };
        return {
          success: false,
          output: err.stdout ?? '',
          error: err.stderr ?? err.message ?? 'Command failed',
          metadata: { durationMs: Date.now() - startTime },
        };
      }
    },
  };
}
