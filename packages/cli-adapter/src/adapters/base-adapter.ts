import { execSync } from 'node:child_process';

export interface ExecOptions {
  timeout?: number;       // ms, default 60000
  cwd?: string;
  env?: Record<string, string>;
  dangerouslySkipPermissions?: boolean;
}

export interface ExecResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  durationMs: number;
}

export type CliState = 'busy' | 'idle' | 'error' | 'question';

export interface AdapterHealth {
  available: boolean;
  binaryPath: string | null;
  version: string | null;
}

export abstract class BaseAdapter {
  abstract readonly name: string;
  abstract readonly binary: string;

  abstract exec(prompt: string, options?: ExecOptions): Promise<ExecResult>;
  abstract detectState(output: string): CliState;

  isAvailable(): boolean {
    try {
      execSync(`which ${this.binary}`, { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }

  getHealth(): AdapterHealth {
    try {
      const binaryPath = execSync(`which ${this.binary}`, { encoding: 'utf8' }).trim();
      let version: string | null = null;
      try {
        version = execSync(`${this.binary} --version 2>/dev/null`, {
          encoding: 'utf8',
          timeout: 3000,
        }).trim();
      } catch {
        // version flag not supported — acceptable
      }
      return { available: true, binaryPath, version };
    } catch {
      return { available: false, binaryPath: null, version: null };
    }
  }
}
