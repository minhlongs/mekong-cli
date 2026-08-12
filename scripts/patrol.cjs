#!/usr/bin/env node
/**
 * mekong patrol — Military camp compliance check
 * Usage: mekong patrol [--fix] [--military]
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const ARCHIVE = path.join(ROOT, '.archive');
const ORPHAN_STALE = ['.agent', '.agents', '.antigravity', '.gemini', '.opencode', '.cursorrules', '.claude-backup', '.claude-skills'];
const STALE_REPORTS = [
  'final-security-compliance-report.md', 'integration_test_report.md',
  'integration_test_report.json', 'phase-4-security-completion-report.md',
  'BACKEND_REFACTORING_REPORT.md', 'GO_LIVE_REPORT.md',
  'PHASE2_REFACTORING_SUMMARY.md', 'PHASE4_INTEGRATION_COMPLETE.md',
  'demo_script.md', 'STRATEGY.md', 'repomix-output.xml'
];

const QUAN_DOANH = [
  'mekong/bootstrap/', 'mekong/init/', 'mekong/audit/',
  'mekong/constitution/', 'mekong/hooks/',
  '.claude/hooks/', '.ck.json'
];

const results = { violations: [], orphans: [], stale_reports: [], integrity: [], duplicate_managers: [], healthy: true };

// 1. Check HÀNH LANG — orphan dirs
console.log('\n🔍 Patrol: Check HÀNH LANG...');
for (const d of ORPHAN_STALE) {
  if (fs.existsSync(path.join(ROOT, d))) {
    results.orphans.push(d);
    results.healthy = false;
  }
}
if (results.orphans.length > 0) {
  console.log(`  ⚠️  ${results.orphans.length} orphan dir(s) found: ${results.orphans.join(', ')}`);
  if (process.argv.includes('--fix')) {
    const archiveDir = path.join(ARCHIVE, 'orphan-dirs');
    fs.mkdirSync(archiveDir, { recursive: true });
    for (const d of results.orphans) {
      fs.renameSync(path.join(ROOT, d), path.join(archiveDir, d));
      console.log(`  ✅ Archived: ${d}`);
    }
    results.orphans = [];
  }
} else {
  console.log('  ✅ HÀNH LANG clean');
}

// 2. Check stale reports
console.log('\n🔍 Patrol: Check stale reports...');
for (const f of STALE_REPORTS) {
  if (fs.existsSync(path.join(ROOT, f))) {
    results.stale_reports.push(f);
    results.healthy = false;
  }
}
if (results.stale_reports.length > 0) {
  console.log(`  ⚠️  ${results.stale_reports.length} stale report(s) found`);
  if (process.argv.includes('--fix')) {
    const archiveDir = path.join(ARCHIVE, 'reports');
    fs.mkdirSync(archiveDir, { recursive: true });
    for (const f of results.stale_reports) {
      fs.renameSync(path.join(ROOT, f), path.join(archiveDir, f));
      console.log(`  ✅ Archived: ${f}`);
    }
    results.stale_reports = [];
  }
} else {
  console.log('  ✅ No stale reports');
}

// 3. Check package manager conflict
console.log('\n🔍 Patrol: Check package managers...');
const hasNpm = fs.existsSync(path.join(ROOT, 'package-lock.json'));
const hasPnpm = fs.existsSync(path.join(ROOT, 'pnpm-lock.yaml'));
if (hasNpm && hasPnpm) {
  results.duplicate_managers = ['package-lock.json', 'pnpm-lock.yaml'];
  results.healthy = false;
  console.log('  ⚠️  Both npm (package-lock.json) and pnpm (pnpm-lock.yaml) present');
} else {
  console.log('  ✅ Single package manager');
}

// 4. Check QUÂN DOANH integrity (git diff against canonical state)
console.log('\n🔍 Patrol: Check QUÂN DOANH integrity...');
try {
  const diff = execSync('git diff --name-only HEAD -- mekong/ .claude/hooks/', { cwd: ROOT, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  if (diff) {
    results.integrity = diff.split('\n').filter(Boolean);
    console.log(`  ⚠️  ${results.integrity.length} QUÂN DOANH file(s) modified:`);
    results.integrity.forEach(f => console.log(`    - ${f}`));
  } else {
    console.log('  ✅ QUÂN DOANH intact');
  }
} catch { /* first commit or no git */ }

// Summary
console.log('\n=== PATROL SUMMARY ===');
console.log(`  Orphans: ${results.orphans.length} ${results.orphans.length > 0 ? '❌' : '✅'}`);
console.log(`  Stale reports: ${results.stale_reports.length} ${results.stale_reports.length > 0 ? '❌' : '✅'}`);
console.log(`  Package conflict: ${results.duplicate_managers.length > 0 ? '❌' : '✅'}`);
console.log(`  QUÂN DOANH integrity: ${results.integrity.length > 0 ? `⚠️  ${results.integrity.length} files modified` : '✅'}`);

if (results.healthy) {
  console.log('\n✅ DOANH TRẠI SẠCH. No violations.');
} else {
  console.log(`\n⚠️  ${results.orphans.length + results.stale_reports.length + (results.duplicate_managers.length > 0 ? 1 : 0)} issue(s) found. Run 'mekong patrol --fix' to auto-resolve.`);
}

process.exit(results.healthy ? 0 : 1);
