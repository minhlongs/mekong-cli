#!/usr/bin/env ts-node
/**
 * Dunning KV Sync Job
 * ROIaaS Phase 5 - Daily dunning sync for license suspension
 *
 * Runs daily to:
 * - Check licenses past grace period
 * - Suspend licenses with max retries exceeded
 * - Log suspension events
 *
 * Usage:
 *   pnpm run sync-dunning-kv
 *   # Or via cron: 0 2 * * * (daily at 2 AM)
 */

import { DunningService } from '../billing/dunning-service';
import { LicenseService } from '../billing/license-service';
import { AuditLogService } from '../audit/audit-log-service';

interface SyncResult {
  timestamp: string;
  checked: number;
  suspended: string[];
  errors: string[];
}

async function runDunningSync(): Promise<SyncResult> {
  const result: SyncResult = {
    timestamp: new Date().toISOString(),
    checked: 0,
    suspended: [],
    errors: [],
  };

  try {
    const dunningService = DunningService.getInstance();
    const licenseService = LicenseService.getInstance();
    const auditService = AuditLogService.getInstance();

    console.log('[Dunning Sync] Starting daily dunning sync...');
    console.log(`[Dunning Sync] Timestamp: ${result.timestamp}`);

    // Check and suspend licenses past grace period
    const suspensionResult = await dunningService.checkAndSuspendExpiredGracePeriods();
    result.checked = suspensionResult.checked;
    result.suspended = suspensionResult.suspended;

    console.log(`[Dunning Sync] Checked ${result.checked} dunning records`);
    console.log(`[Dunning Sync] Suspended ${result.suspended.length} licenses`);

    if (result.suspended.length > 0) {
      console.log(`[Dunning Sync] Suspended license IDs: ${result.suspended.join(', ')}`);

      // Log batch suspension event
      await auditService.log('system', 'rate_limit', {
        metadata: {
          eventType: 'dunning_sync_batch',
          suspendedCount: result.suspended.length,
          suspendedLicenseIds: result.suspended,
          syncTimestamp: result.timestamp,
        },
      });
    }

    // Summary
    const allLicenses = await licenseService.listLicenses({ status: 'all' });
    const suspendedCount = allLicenses.licenses.filter(
      (l) => l.status === 'revoked'
    ).length;

    console.log(`[Dunning Sync] Total suspended licenses: ${suspendedCount}`);
    console.log('[Dunning Sync] Sync completed successfully');

    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    result.errors.push(errorMessage);
    console.error('[Dunning Sync] Error during sync:', errorMessage);

    return result;
  }
}

// Main execution
async function main() {
  console.log('='.repeat(60));
  console.log('DUNNING KV SYNC - Daily License Suspension Check');
  console.log('='.repeat(60));

  const result = await runDunningSync();

  console.log('='.repeat(60));
  console.log('SYNC SUMMARY');
  console.log('='.repeat(60));
  console.log(`Timestamp:    ${result.timestamp}`);
  console.log(`Checked:      ${result.checked} records`);
  console.log(`Suspended:    ${result.suspended.length} licenses`);
  console.log(`Errors:       ${result.errors.length}`);
  console.log('='.repeat(60));

  if (result.errors.length > 0) {
    console.error('ERRORS:');
    result.errors.forEach((err, i) => {
      console.error(`  ${i + 1}. ${err}`);
    });
    process.exit(1);
  }

  process.exit(0);
}

// Run if executed directly
if (require.main === module) {
  main().catch((error) => {
    console.error('[Dunning Sync] Fatal error:', error);
    process.exit(1);
  });
}

export { runDunningSync };
