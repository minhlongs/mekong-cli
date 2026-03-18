import { spawn } from 'node:child_process';
import { BaseAdapter, type ExecOptions, type ExecResult, type CliState } from './base-adapter.ts';

const DEFAULT_TIMEOUT = 60_000;

// CC CLI v2.1.38+ uses Ink TUI — must use -p (print mode) for non-interactive use
export class ClaudeCliAdapter extends BaseAdapter {
  readonly name = 'claude';
  readonly binary = 'claude';

  exec(prompt: string, options: ExecOptions = {}): Promise<ExecResult> {
    return new Promise((resolve, reject) => {
      const start = Date.now();
      const args = ['-p', prompt];
      if (options.dangerouslySkipPermissions) {
        args.unshift('--dangerously-skip-permissions');
      }

      const child = spawn(this.binary, args, {
        cwd: options.cwd,
        env: { ...process.env, ...(options.env ?? {}) },
        stdio: ['ignore', 'pipe', 'pipe'], // stdin MUST be 'ignore' — piped stdin causes infinite hang
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (chunk: Buffer) => { stdout += chunk.toString(); });
      child.stderr.on('data', (chunk: Buffer) => { stderr += chunk.toString(); });

      const timer = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`claude -p timed out after ${options.timeout ?? DEFAULT_TIMEOUT}ms`));
      }, options.timeout ?? DEFAULT_TIMEOUT);

      child.on('close', (exitCode) => {
        clearTimeout(timer);
        resolve({ stdout, stderr, exitCode: exitCode ?? 1, durationMs: Date.now() - start });
      });

      child.on('error', (err) => {
        clearTimeout(timer);
        reject(err);
      });
    });
  }

  detectState(output: string): CliState {
    if (/cooking|thinking|planning|executing/i.test(output)) return 'busy';
    if (/\berror\b|failed|exception/i.test(output)) return 'error';
    if (/\?$|\(y\/n\)|confirm|proceed/i.test(output)) return 'question';
    if (/[❯>]\s*$/.test(output) || output.trim() === '') return 'idle';
    return 'busy';
  }
}
