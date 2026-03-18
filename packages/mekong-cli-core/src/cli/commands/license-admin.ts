/**
 * `mekong license-admin` — Admin subcommands for license key management.
 *
 *   mekong license-admin create --tier pro --owner user@example.com [--days 365]
 *   mekong license-admin list
 *   mekong license-admin revoke <key-id>
 *   mekong license-admin rotate <key-id>
 *   mekong license-admin audit [--key <key-id>]
 *
 * Access: requires enterprise tier OR MEKONG_ADMIN_SECRET env var.
 */
import { join } from 'node:path';
import { homedir } from 'node:os';
import type { Command } from 'commander';
import { LicenseAdmin } from '../../license/admin.js';
import { LicenseGate } from '../../license/gate.js';
import type { LicenseTier } from '../../license/types.js';

const VALID_TIERS: LicenseTier[] = ['free', 'starter', 'pro', 'enterprise'];
const DEFAULT_REGISTRY = join(homedir(), '.mekong', 'admin', 'keys.json');
const DEFAULT_AUDIT_LOG = join(homedir(), '.mekong', 'admin', 'audit.jsonl');

async function checkAdminAccess(): Promise<boolean> {
  if (process.env['MEKONG_ADMIN_SECRET']) return true;
  const gate = new LicenseGate();
  const result = await gate.validate();
  if (!result.ok) return false;
  return result.value.tier === 'enterprise';
}

function makeAdmin(operator?: string): LicenseAdmin {
  return new LicenseAdmin(DEFAULT_REGISTRY, DEFAULT_AUDIT_LOG, operator ?? 'cli');
}

export function registerLicenseAdminCommand(program: Command): void {
  const admin = program
    .command('license-admin')
    .description('Admin: create, revoke, list, rotate license keys (requires enterprise or MEKONG_ADMIN_SECRET)');

  admin
    .command('create')
    .description('Generate a new signed license key')
    .requiredOption('--tier <tier>', 'License tier (free|starter|pro|enterprise)')
    .requiredOption('--owner <owner>', 'Owner identifier (email or name)')
    .option('--brand <brand>', 'Brand prefix (MEKONG|SOPHIA|WELL|APEX|ALGO|OPENCLAW|AGENCYOS)', 'MEKONG')
    .option('--days <days>', 'Validity in days', '365')
    .option('--operator <operator>', 'Operator identifier for audit log', 'cli')
    .action(async (opts: { tier: string; owner: string; brand: string; days: string; operator: string }) => {
      if (!(await checkAdminAccess())) {
        console.error('Access denied. Requires enterprise tier or MEKONG_ADMIN_SECRET.');
        process.exit(1);
      }
      if (!VALID_TIERS.includes(opts.tier as LicenseTier)) {
        console.error(`Invalid tier: ${opts.tier}. Must be one of: ${VALID_TIERS.join(', ')}`);
        process.exit(1);
      }
      const a = makeAdmin(opts.operator);
      const result = await a.createKey(opts.tier as LicenseTier, opts.owner, parseInt(opts.days, 10));
      if (!result.ok) {
        console.error('Failed to create key:', result.error.message);
        process.exit(1);
      }
      const k = result.value;
      console.log('\nKey created:');
      console.log(`  Key     : ${k.key}`);
      console.log(`  Tier    : ${k.tier}`);
      console.log(`  Owner   : ${k.owner}`);
      console.log(`  Expires : ${k.expiresAt}`);
      console.log('\nJSON (for mekong license activate --key):');
      console.log(JSON.stringify(k));
      console.log('');
    });

  admin
    .command('list')
    .description('List all issued license keys')
    .option('--operator <operator>', 'Operator identifier', 'cli')
    .action(async (opts: { operator: string }) => {
      if (!(await checkAdminAccess())) {
        console.error('Access denied. Requires enterprise tier or MEKONG_ADMIN_SECRET.');
        process.exit(1);
      }
      const a = makeAdmin(opts.operator);
      const result = await a.listKeys();
      if (!result.ok) {
        console.error('Failed to list keys:', result.error.message);
        process.exit(1);
      }
      const keys = result.value;
      if (keys.length === 0) {
        console.log('\nNo keys found.\n');
        return;
      }
      console.log(`\n${keys.length} key(s):\n`);
      for (const k of keys) {
        console.log(`  ${k.key}  tier=${k.tier}  status=${k.status}  owner=${k.owner}  expires=${k.expiresAt}`);
      }
      console.log('');
    });

  admin
    .command('revoke')
    .description('Revoke a license key by key-id')
    .argument('<key-id>', 'The RAAS-xxx key identifier')
    .option('--operator <operator>', 'Operator identifier', 'cli')
    .action(async (keyId: string, opts: { operator: string }) => {
      if (!(await checkAdminAccess())) {
        console.error('Access denied. Requires enterprise tier or MEKONG_ADMIN_SECRET.');
        process.exit(1);
      }
      const a = makeAdmin(opts.operator);
      const result = await a.revokeKey(keyId);
      if (!result.ok) {
        console.error('Failed to revoke key:', result.error.message);
        process.exit(1);
      }
      console.log(`\nKey revoked: ${keyId}\n`);
    });

  admin
    .command('rotate')
    .description('Rotate a license key (revoke old, issue new with same tier/owner/remaining days)')
    .argument('<key-id>', 'The RAAS-xxx key identifier')
    .option('--operator <operator>', 'Operator identifier', 'cli')
    .action(async (keyId: string, opts: { operator: string }) => {
      if (!(await checkAdminAccess())) {
        console.error('Access denied. Requires enterprise tier or MEKONG_ADMIN_SECRET.');
        process.exit(1);
      }
      const a = makeAdmin(opts.operator);
      const result = await a.rotateKey(keyId);
      if (!result.ok) {
        console.error('Failed to rotate key:', result.error.message);
        process.exit(1);
      }
      const k = result.value;
      console.log('\nKey rotated:');
      console.log(`  Old key : ${keyId} (revoked)`);
      console.log(`  New key : ${k.key}`);
      console.log(`  Tier    : ${k.tier}`);
      console.log(`  Expires : ${k.expiresAt}`);
      console.log('\nJSON:');
      console.log(JSON.stringify(k));
      console.log('');
    });

  admin
    .command('stats')
    .description('License key statistics: issued, active, revoked, revenue estimate')
    .option('--operator <operator>', 'Operator identifier', 'cli')
    .action(async (opts: { operator: string }) => {
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

      // Breakdown by tier
      const byTier = new Map<string, number>();
      for (const k of active) byTier.set(k.tier, (byTier.get(k.tier) ?? 0) + 1);
      console.log('\n  By Tier:');
      for (const [tier, count] of byTier) {
        console.log(`    ${tier}: ${count} active ($${(tierPrices[tier] ?? 0) * count}/mo)`);
      }
      console.log('');
    });

  admin
    .command('audit')
    .description('Show audit log entries')
    .option('--key <key-id>', 'Filter by key-id')
    .option('--operator <operator>', 'Operator identifier', 'cli')
    .action(async (opts: { key?: string; operator: string }) => {
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
    });
}
