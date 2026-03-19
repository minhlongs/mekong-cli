import { spawn } from 'node:child_process';
import { BaseAdapter, type ExecOptions, type ExecResult, type CliState } from './base-adapter.js';

const DEFAULT_TIMEOUT = 60_000;

export class QwenCliAdapter extends BaseAdapter {
  readonly name = 'qwen';
  readonly binary = 'qwen';

  exec(prompt: string, options: ExecOptions = {}): Promise<ExecResult> {
    return new Promise((resolve, reject) => {
      const start = Date.now();
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
        reject(new Error(`qwen -p timed out after ${options.timeout ?? DEFAULT_TIMEOUT}ms`));
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
    if (/thinking|running|working/i.test(output)) return 'busy';
    if (/\berror\b|failed|exception/i.test(output)) return 'error';
    if (/\?$|confirm|proceed/i.test(output)) return 'question';
    if (/[>$]\s*$/.test(output) || output.trim() === '') return 'idle';
    return 'busy';
  }
}
