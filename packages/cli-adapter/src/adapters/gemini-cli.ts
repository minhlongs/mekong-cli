import { spawn } from 'node:child_process';
import { BaseAdapter, type ExecOptions, type ExecResult, type CliState } from './base-adapter.ts';

const DEFAULT_TIMEOUT = 60_000;

export class GeminiCliAdapter extends BaseAdapter {
  readonly name = 'gemini';
  readonly binary = 'gemini';

  exec(prompt: string, options: ExecOptions = {}): Promise<ExecResult> {
    return new Promise((resolve, reject) => {
      const start = Date.now();
      // gemini CLI: use -p flag for non-interactive print mode
      const child = spawn(this.binary, ['-p', prompt], {
        cwd: options.cwd,
        env: { ...process.env, ...(options.env ?? {}) },
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (chunk: Buffer) => { stdout += chunk.toString(); });
      child.stderr.on('data', (chunk: Buffer) => { stderr += chunk.toString(); });

      const timer = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`gemini -p timed out after ${options.timeout ?? DEFAULT_TIMEOUT}ms`));
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
    if (/generating|processing|loading/i.test(output)) return 'busy';
    if (/\berror\b|failed|invalid/i.test(output)) return 'error';
    if (/\?$|\(yes\/no\)|confirm/i.test(output)) return 'question';
    if (/[>$]\s*$/.test(output) || output.trim() === '') return 'idle';
    return 'busy';
  }
}
