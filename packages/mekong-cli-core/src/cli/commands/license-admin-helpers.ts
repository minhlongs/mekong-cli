/**
 * license-admin-helpers.ts — Access control, factory, and stats/audit handlers for license-admin CLI.
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import { LicenseAdmin } from '../../license/admin.js';
import { LicenseGate } from '../../license/gate.js';
import type { LicenseTier } from '../../license/types.js';

export const VALID_TIERS: LicenseTier[] = ['free', 'starter', 'pro', 'enterprise'];
export const DEFAULT_REGISTRY = join(homedir(), '.mekong', 'admin', 'keys.json');
export const DEFAULT_AUDIT_LOG = join(homedir(), '.mekong', 'admin', 'audit.jsonl');

export async function checkAdminAccess(): Promise<boolean> {
  if (process.env['MEKONG_ADMIN_SECRET']) return true;
  const gate = new LicenseGate();
  const result = await gate.validate();
  if (!result.ok) return false;
  return result.value.tier === 'enterprise';
}

export function makeAdmin(operator?: string): LicenseAdmin {
  return new LicenseAdmin(DEFAULT_REGISTRY, DEFAULT_AUDIT_LOG, operator ?? 'cli');
}

export async function runLicenseAdminStats(opts: { operator: string }): Promise<void> {
  if (!(await checkAdminAccess())) {
    console.error('Access denied.');
    process.exit(1);
  }
  const a = makeAdmin(opts.operator);
  const result = await a.listKeys();
  if (!result.ok) {
    console.error('Failed to list keys:', result.error.message);
    process.exit(1);
  }
  const keys = result.value;
  const active = keys.filter(k => k.status === 'active');
  const revoked = keys.filter(k => k.status === 'revoked');
  const expired = keys.filter(k => k.status === 'expired');
  const tierPrices: Record<string, number> = { free: 0, starter: 29, pro: 99, enterprise: 299 };
  const estimatedMRR = active.reduce((sum, k) => sum + (tierPrices[k.tier] ?? 0), 0);

  console.log('\n── License Key Stats ──');
  console.log(`  Total issued : ${keys.length}`);
  console.log(`  Active       : ${active.length}`);
  console.log(`  Revoked      : ${revoked.length}`);
  console.log(`  Expired      : ${expired.length}`);
  console.log(`  Est. MRR     : $${estimatedMRR}/mo`);
  console.log(`  Est. ARR     : $${estimatedMRR * 12}/yr`);

  const byTier = new Map<string, number>();
  for (const k of active) byTier.set(k.tier, (byTier.get(k.tier) ?? 0) + 1);
  console.log('\n  By Tier:');
  for (const [tier, count] of byTier) {
    console.log(`    ${tier}: ${count} active ($${(tierPrices[tier] ?? 0) * count}/mo)`);
  }
  console.log('');
}

export async function runLicenseAdminAudit(opts: { key?: string; operator: string }): Promise<void> {
  if (!(await checkAdminAccess())) {
    console.error('Access denied. Requires enterprise tier or MEKONG_ADMIN_SECRET.');
    process.exit(1);
  }
  const { AuditLog } = await import('../../license/audit-log.js');
  const log = new AuditLog(DEFAULT_AUDIT_LOG);
  const result = opts.key ? await log.readByKey(opts.key) : await log.readAll();
  if (!result.ok) {
    console.error('Failed to read audit log:', result.error.message);
    process.exit(1);
  }
  const entries = result.value;
  if (entries.length === 0) {
    console.log('\nNo audit entries found.\n');
    return;
  }
  console.log(`\n${entries.length} audit entry(ies):\n`);
  for (const e of entries) {
    const detail = e.details ? `  ${JSON.stringify(e.details)}` : '';
    console.log(`  [${e.timestamp}] ${e.action.padEnd(8)} key=${e.keyId}  op=${e.operator}${detail}`);
  }
  console.log('');
}
