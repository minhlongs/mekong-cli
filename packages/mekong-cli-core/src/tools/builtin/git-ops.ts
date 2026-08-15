import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import type { ToolDefinition, ToolResult } from '../../types/tool.js';

const execAsync = promisify(exec);

const BLOCKED_GIT_ARGS = ['push --force', 'reset --hard', 'clean -f'];

export function createGitTool(): ToolDefinition {
  return {
    name: 'git',
    description: 'Execute git commands (safe subset — force-push, reset --hard, clean -f blocked)',
    category: 'shell',
    securityLevel: 1,
    params: [
      {
        name: 'command',
        type: 'string',
        description: 'Git subcommand and args (e.g. "status", "diff", "log --oneline -5")',
        required: true,
      },
    ],
    execute: async (params): Promise<ToolResult> => {
      const subcommand = params.command as string;

      for (const blocked of BLOCKED_GIT_ARGS) {
        if (subcommand.includes(blocked)) {
          return { success: false, output: '', error: `Blocked: git ${blocked}` };
        }
      }

      try {
        const { stdout, stderr } = await execAsync(`git ${subcommand}`, { timeout: 15000 });
        return {
          success: true,
          output: stdout + (stderr ? `\n${stderr}` : ''),
        };
      } catch (error: unknown) {
        const err = error as { stdout?: string; stderr?: string; message?: string };
        return {
          success: false,
          output: err.stdout ?? '',
          error: err.stderr ?? err.message ?? 'Git command failed',
        };
      }
    },
  };
}
