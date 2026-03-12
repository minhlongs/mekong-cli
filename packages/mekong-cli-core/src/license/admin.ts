/**
 * LicenseAdmin — create/revoke/list/rotate keys in admin registry.
 * Phase 2 of v0.5 License Admin.
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname } from 'node:path';
import type { LicenseTier, LicenseKey } from './types.js';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import { generateKey } from './key-generator.js';
import { AuditLog } from './audit-log.js';
import { verifyLicense } from './verifier.js';

export interface AdminRegistry {
  keys: LicenseKey[];
}

export class LicenseAdmin {
  private readonly auditLog: AuditLog;

  constructor(
    private readonly registryPath: string,
    private readonly auditLogPath: string,
    private readonly operator: string = 'admin',
  ) {
    this.auditLog = new AuditLog(auditLogPath);
  }

  // ── Registry helpers ──────────────────────────────────────────────────────

  private async loadRegistry(): Promise<AdminRegistry> {
    try {
      if (!existsSync(this.registryPath)) return { keys: [] };
      const raw = await readFile(this.registryPath, 'utf-8');
      return JSON.parse(raw) as AdminRegistry;
    } catch {
      return { keys: [] };
    }
  }

  private async saveRegistry(reg: AdminRegistry): Promise<Result<void, Error>> {
    try {
      await mkdir(dirname(this.registryPath), { recursive: true });
      await writeFile(this.registryPath, JSON.stringify(reg, null, 2), { mode: 0o600 });
      return ok(undefined);
    } catch (e) {
      return err(new Error(`Failed to save registry: ${String(e)}`));
    }
  }

  // ── Public API ────────────────────────────────────────────────────────────

  /**
   * Create a new signed license key and persist it to the registry.
   * @param tier - license tier to assign
   * @param owner - owner identifier (email or ID)
   * @param expiryDays - validity period in days (default 365)
   */
  async createKey(
    tier: LicenseTier,
    owner: string,
    expiryDays = 365,
  ): Promise<Result<LicenseKey, Error>> {
    const key = generateKey({ tier, owner, expiryDays });
    const reg = await this.loadRegistry();
    reg.keys.push(key);
    const saved = await this.saveRegistry(reg);
    if (!saved.ok) return saved;
    await this.auditLog.append({
      action: 'create',
      keyId: key.key,
      operator: this.operator,
      details: { tier, owner, expiryDays },
    });
    return ok(key);
  }

  /** Revoke an existing key by ID; returns error if key not found. */
  async revokeKey(keyId: string): Promise<Result<void, Error>> {
    const reg = await this.loadRegistry();
    const idx = reg.keys.findIndex((k) => k.key === keyId);
    if (idx === -1) return err(new Error(`Key not found: ${keyId}`));
    reg.keys[idx] = { ...reg.keys[idx]!, status: 'revoked' };
    const saved = await this.saveRegistry(reg);
    if (!saved.ok) return saved;
    await this.auditLog.append({ action: 'revoke', keyId, operator: this.operator });
    return ok(undefined);
  }

  /** List all keys in the registry (active and revoked). */
  async listKeys(): Promise<Result<LicenseKey[], Error>> {
    const reg = await this.loadRegistry();
    return ok(reg.keys);
  }

  /** Revoke old key and issue a new one with the same tier/owner and prorated expiry. */
  async rotateKey(keyId: string): Promise<Result<LicenseKey, Error>> {
    const reg = await this.loadRegistry();
    const old = reg.keys.find((k) => k.key === keyId);
    if (!old) return err(new Error(`Key not found: ${keyId}`));

    // Revoke old
    const revokeIdx = reg.keys.findIndex((k) => k.key === keyId);
    reg.keys[revokeIdx] = { ...old, status: 'revoked' };

    // Compute remaining days from old key
    const remainingMs = Math.max(0, new Date(old.expiresAt).getTime() - Date.now());
    const remainingDays = Math.ceil(remainingMs / 86_400_000) || 1;

    // Create replacement
    const newKey = generateKey({ tier: old.tier, owner: old.owner, expiryDays: remainingDays });
    reg.keys.push(newKey);

    const saved = await this.saveRegistry(reg);
    if (!saved.ok) return saved;

    await this.auditLog.append({
      action: 'rotate',
      keyId,
      operator: this.operator,
      details: { newKeyId: newKey.key },
    });
    return ok(newKey);
  }

  // ── Phase 6 enhancements ──────────────────────────────────────────────────

  /** Validate all keys in the registry; returns per-key validity status. */
  async validateAll(): Promise<Result<Array<{ key: LicenseKey; valid: boolean; message?: string }>, Error>> {
    const reg = await this.loadRegistry();
    const results = reg.keys.map((k) => {
      const v = verifyLicense(k);
      return { key: k, valid: v.valid, message: v.message };
    });
    return ok(results);
  }

  /**
   * List active keys expiring within the given number of days.
   * @param withinDays - lookahead window in days
   */
  async listExpiring(withinDays: number): Promise<Result<LicenseKey[], Error>> {
    const reg = await this.loadRegistry();
    const cutoff = Date.now() + withinDays * 86_400_000;
    const expiring = reg.keys.filter((k) => {
      if (k.status === 'revoked') return false;
      const exp = new Date(k.expiresAt).getTime();
      return exp > Date.now() && exp <= cutoff;
    });
    return ok(expiring);
  }
}
