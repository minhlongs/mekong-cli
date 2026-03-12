/**
 * AuditLog — append-only JSONL audit trail for license operations.
 * Phase 3 of v0.5 License Admin.
 */
import { appendFile, readFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';

export type AuditAction = 'create' | 'revoke' | 'rotate' | 'validate';

export interface AuditEntry {
  timestamp: string;
  action: AuditAction;
  keyId: string;
  operator: string;
  details?: Record<string, unknown>;
}

export class AuditLog {
  constructor(private readonly logPath: string) {}

  async append(entry: Omit<AuditEntry, 'timestamp'>): Promise<Result<void, Error>> {
    try {
      await mkdir(dirname(this.logPath), { recursive: true });
      const record: AuditEntry = { timestamp: new Date().toISOString(), ...entry };
      await appendFile(this.logPath, JSON.stringify(record) + '\n');
      return ok(undefined);
    } catch (e) {
      return err(new Error(`Failed to write audit log: ${String(e)}`));
    }
  }

  async readAll(): Promise<Result<AuditEntry[], Error>> {
    try {
      const content = await readFile(this.logPath, 'utf-8');
      const entries = content
        .trim()
        .split('\n')
        .filter((l) => l.trim())
        .map((l) => JSON.parse(l) as AuditEntry);
      return ok(entries);
    } catch (e: unknown) {
      if ((e as NodeJS.ErrnoException).code === 'ENOENT') return ok([]);
      return err(new Error(`Failed to read audit log: ${String(e)}`));
    }
  }

  async readByKey(keyId: string): Promise<Result<AuditEntry[], Error>> {
    const all = await this.readAll();
    if (!all.ok) return all;
    return ok(all.value.filter((e) => e.keyId === keyId));
  }
}
