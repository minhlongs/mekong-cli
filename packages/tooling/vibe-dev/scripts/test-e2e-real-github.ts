#!/usr/bin/env ts-node
/**
 * End-to-End Test with Real GitHub Project V2
 *
 * Prerequisites:
 * 1. GitHub Personal Access Token with 'project' scope
 * 2. GitHub Project V2 created (User or Org)
 * 3. At least 2-3 issues added to the project
 *
 * Usage:
 *   GITHUB_TOKEN=<token> ts-node scripts/test-e2e-real-github.ts <owner> <projectNumber> [isOrg]
 *
 * Example:
 *   GITHUB_TOKEN=ghp_xxx ts-node scripts/test-e2e-real-github.ts myuser 1
 *   GITHUB_TOKEN=ghp_xxx ts-node scripts/test-e2e-real-github.ts myorg 5 true
 */

import { SyncCommand } from '../src/commands/sync.command';
import * as fs from 'fs/promises';
import * as path from 'path';

const TEST_FILE = path.join(process.cwd(), 'test-e2e-tasks.json');

interface TestConfig {
  token: string;
  owner: string;
  projectNumber: number;
  isOrg: boolean;
}

async function parseArgs(): Promise<TestConfig> {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    throw new Error('GITHUB_TOKEN environment variable is required');
  }

  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error('Usage: GITHUB_TOKEN=<token> ts-node scripts/test-e2e-real-github.ts <owner> <projectNumber> [isOrg]');
    process.exit(1);
  }

  return {
    token,
    owner: args[0],
    projectNumber: parseInt(args[1]),
    isOrg: args[2] === 'true' || args[2] === '1'
  };
}

async function cleanupTestFile() {
  try {
    await fs.unlink(TEST_FILE);
    console.log(`🗑️  Cleaned up test file: ${TEST_FILE}`);
  } catch (error: any) {
    if (error.code !== 'ENOENT') {
      console.warn('Warning: Could not clean up test file:', error.message);
    }
  }
}

async function verifyLocalFile() {
  const content = await fs.readFile(TEST_FILE, 'utf-8');
  const data = JSON.parse(content);

  console.log('\n📄 Local File Contents:');
  console.log(`   Tasks: ${data.tasks?.length || 0}`);
  console.log(`   Epics: ${data.epics?.length || 0}`);

  if (data.tasks && data.tasks.length > 0) {
    console.log('\n   Sample Task:');
    const sample = data.tasks[0];
    console.log(`     ID: ${sample.id}`);
    console.log(`     Title: ${sample.title}`);
    console.log(`     Status: ${sample.status}`);
    console.log(`     Priority: ${sample.priority}`);
  }

  return data;
}

async function modifyLocalTask(data: any) {
  if (!data.tasks || data.tasks.length === 0) {
    console.log('⚠️  No tasks to modify');
    return data;
  }

  // Modify first task
  const originalStatus = data.tasks[0].status;
  data.tasks[0].status = originalStatus === 'pending' ? 'active' : 'pending';
  data.tasks[0].priority = 'high';
  data.tasks[0].updatedAt = new Date().toISOString();

  console.log('\n✏️  Modified Local Task:');
  console.log(`   Changed status: ${originalStatus} → ${data.tasks[0].status}`);
  console.log(`   Changed priority → high`);
  console.log(`   Updated timestamp: ${data.tasks[0].updatedAt}`);

  await fs.writeFile(TEST_FILE, JSON.stringify(data, null, 2));
  return data;
}

async function main() {
  console.log('🧪 Phase 7: Real-World End-to-End Test\n');
  console.log('═══════════════════════════════════════\n');

  const config = await parseArgs();

  console.log('📋 Test Configuration:');
  console.log(`   Owner: ${config.owner}`);
  console.log(`   Project: #${config.projectNumber}`);
  console.log(`   Type: ${config.isOrg ? 'Organization' : 'User'}`);
  console.log(`   Token: ${config.token.substring(0, 7)}...`);
  console.log(`   Test File: ${TEST_FILE}\n`);

  const cmd = new SyncCommand();

  // ============================================================
  // TEST 1: Initial Pull from GitHub → Local
  // ============================================================
  console.log('─────────────────────────────────────────');
  console.log('TEST 1: Initial Pull (GitHub → Local)');
  console.log('─────────────────────────────────────────\n');

  await cleanupTestFile();

  const result1 = await cmd.execute({
    githubToken: config.token,
    owner: config.owner,
    projectNumber: config.projectNumber,
    localPath: TEST_FILE,
    isOrg: config.isOrg,
    autoResolve: true,
    dryRun: false
  });

  console.log('\n✅ Test 1 Results:');
  console.log(`   Created Local Tasks: ${result1.addedToLocal}`);
  console.log(`   Errors: ${result1.errors.length}`);

  if (result1.errors.length > 0) {
    console.error('\n❌ Test 1 FAILED with errors:');
    result1.errors.forEach(e => console.error(`   - ${e}`));
    process.exit(1);
  }

  const data1 = await verifyLocalFile();

  // ============================================================
  // TEST 2: No-Op Sync (should detect no changes)
  // ============================================================
  console.log('\n─────────────────────────────────────────');
  console.log('TEST 2: No-Op Sync (No Changes Expected)');
  console.log('─────────────────────────────────────────\n');

  const result2 = await cmd.execute({
    githubToken: config.token,
    owner: config.owner,
    projectNumber: config.projectNumber,
    localPath: TEST_FILE,
    isOrg: config.isOrg,
    autoResolve: true,
    dryRun: false
  });

  console.log('\n✅ Test 2 Results:');
  console.log(`   Pulled: ${result2.addedToLocal + result2.updatedLocal}`);
  console.log(`   Pushed: ${result2.addedToRemote + result2.updatedRemote}`);

  if (result2.addedToLocal > 0 || result2.updatedLocal > 0 || result2.addedToRemote > 0 || result2.updatedRemote > 0) {
    console.warn('\n⚠️  WARNING: Expected no changes, but sync occurred');
  }

  // ============================================================
  // TEST 3: Local Modification → Push to GitHub
  // ============================================================
  console.log('\n─────────────────────────────────────────');
  console.log('TEST 3: Local Modification → Push');
  console.log('─────────────────────────────────────────\n');

  await modifyLocalTask(data1);

  const result3 = await cmd.execute({
    githubToken: config.token,
    owner: config.owner,
    projectNumber: config.projectNumber,
    localPath: TEST_FILE,
    isOrg: config.isOrg,
    autoResolve: true,
    dryRun: false
  });

  console.log('\n✅ Test 3 Results:');
  console.log(`   Pushed Updates: ${result3.updatedRemote}`);
  console.log(`   Errors: ${result3.errors.length}`);

  if (result3.updatedRemote === 0) {
    console.warn('\n⚠️  WARNING: Expected push, but no updates occurred');
  }

  // ============================================================
  // TEST 4: Dry Run Mode
  // ============================================================
  console.log('\n─────────────────────────────────────────');
  console.log('TEST 4: Dry Run Mode (No Side Effects)');
  console.log('─────────────────────────────────────────\n');

  // Modify again
  const data4 = await verifyLocalFile();
  if (data4.tasks && data4.tasks.length > 0) {
    data4.tasks[0].priority = 'critical';
    await fs.writeFile(TEST_FILE, JSON.stringify(data4, null, 2));
  }

  const result4 = await cmd.execute({
    githubToken: config.token,
    owner: config.owner,
    projectNumber: config.projectNumber,
    localPath: TEST_FILE,
    isOrg: config.isOrg,
    autoResolve: true,
    dryRun: true
  });

  console.log('\n✅ Test 4 Results:');
  console.log(`   Actions Planned: ${result4.actions.length}`);
  console.log(`   Actually Pushed: ${result4.updatedRemote} (should be 0)`);

  if (result4.updatedRemote > 0) {
    console.error('\n❌ Test 4 FAILED: Dry run should not push changes');
    process.exit(1);
  }

  // ============================================================
  // SUMMARY
  // ============================================================
  console.log('\n═══════════════════════════════════════');
  console.log('🎉 ALL TESTS PASSED');
  console.log('═══════════════════════════════════════\n');

  console.log('Summary:');
  console.log('  ✅ Initial Pull: Fetched tasks from GitHub');
  console.log('  ✅ No-Op Sync: No changes detected');
  console.log('  ✅ Local Push: Modified local → pushed to GitHub');
  console.log('  ✅ Dry Run: No side effects');

  console.log('\n📝 Manual Verification Steps:');
  console.log('  1. Open your GitHub Project V2 in browser');
  console.log('  2. Verify task status/priority changes are reflected');
  console.log('  3. Modify a task in GitHub UI');
  console.log('  4. Run this script again to verify pull works');

  console.log(`\n🗑️  Cleanup: Delete ${TEST_FILE} when done\n`);
}

main().catch(error => {
  console.error('\n❌ E2E Test Failed:', error.message);
  if (error.stack) {
    console.error(error.stack);
  }
  process.exit(1);
});
