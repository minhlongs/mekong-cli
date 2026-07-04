#!/usr/bin/env node
/**
 * mekong audit — Audit project against ZenOS Constitution
 * Usage: mekong audit [path] [--fix]
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const target = path.resolve(process.argv[2] || '.');
const fix = process.argv.includes('--fix');
const MEKONG_ROOT = path.resolve(__dirname, '../..');

const results = [];
function check(name, pass, detail) {
  results.push({ name, pass, detail });
  const icon = pass ? '✅' : '❌';
  console.log(`  ${icon} ${name}${detail ? ' — ' + detail : ''}`);
}

function checkFix(name, fn) {
  if (!fix) return;
  try { fn(); console.log(`     🔧 Fixed: ${name}`); } catch(e) { console.log(`     ⚠ Fix failed: ${e.message}`); }
}

function run(cmd, cwd) {
  try { return execSync(cmd, { cwd: cwd || target, stdio: 'pipe', encoding: 'utf8' }).trim(); }
  catch { return ''; }
}

function main() {
  const isGit = fs.existsSync(path.join(target, '.git'));
  const hasClaude = fs.existsSync(path.join(target, '.claude'));

  console.log(`\n ZenOS Audit: ${path.basename(target)}`);
  console.log(` ${fix ? 'Fix mode' : 'Check only'} (add --fix to auto-correct)\n`);

  // 1. CK Init
  console.log(' [CK Init]');
  check('.claude/ exists', hasClaude);
  check('.ck.json exists', fs.existsSync(path.join(target, '.ck.json')));
  if (hasClaude) {
    const hooks = fs.existsSync(path.join(target, '.claude/hooks'))
      ? fs.readdirSync(path.join(target, '.claude/hooks')).filter(f => f.endsWith('.cjs')) : [];
    check(`hooks (.cjs): ${hooks.length}`, hooks.length > 3, hooks.length + ' hooks');
  }

  // 2. Git
  console.log('\n [Git]');
  check('git repo', isGit);
  if (isGit) {
    const branch = run('git branch --show-current');
    check('on main branch', branch === 'main', branch || '?');
    const remotes = run('git remote -v');
    check('remote configured', !!remotes, remotes.split('\n')[0] || '');
  }

  // 3. 2-Guard Workflow
  console.log('\n [2-Guard Deploy]');
  const wfDir = path.join(target, '.github/workflows');
  const hasGuard = fs.existsSync(path.join(wfDir, 'deploy-2-guard.yml'));
  check('deploy-2-guard.yml', hasGuard);
  if (!hasGuard && fix) {
    checkFix('deploy-2-guard.yml', () => {
      const src = path.join(MEKONG_ROOT, 'mekong/init/skel/.github/workflows/deploy-2-guard.yml');
      fs.mkdirSync(wfDir, { recursive: true });
      fs.copyFileSync(src, path.join(wfDir, 'deploy-2-guard.yml'));
    });
  }

  // 4. Constitution
  console.log('\n [Constitution]');
  check('ZENOS.md exists', fs.existsSync(path.join(target, 'ZENOS.md')));

  // 5. Branch Protection (via gh)
  console.log('\n [Branch Protection]');
  const ghRemote = run('git config --get remote.origin.url').replace(':', '/').replace('git@', 'https://');
  const match = ghRemote.match(/github\.com[:/]([^/]+)\/([^.]+)/);
  if (match) {
    const repo = `${match[1]}/${match[2]}`;
    const prot = run(`gh api repos/${repo}/branches/main/protection 2>/dev/null`, target);
    if (prot) {
      check('PR required', prot.includes('required_pull_request_reviews'), '1 approval');
      check('CI checks required', prot.includes('guard-1-ci'), 'guard-1-ci + guard-2-deploy');
      check('Linear history', prot.includes('required_linear_history'));
    } else {
      check('Branch protection', false, 'Not configured — run: mekong audit . --fix');
      if (fix) {
        checkFix('branch protection', () => {
          const data = JSON.stringify({
            required_status_checks: { strict: true, checks: [{ context: 'guard-1-ci' }, { context: 'guard-2-deploy' }] },
            enforce_admins: true,
            required_pull_request_reviews: { required_approving_review_count: 1, require_last_push_approval: true },
            restrictions: null,
            required_linear_history: true,
            allow_force_pushes: false
          });
          run(`gh api repos/${repo}/branches/main/protection --method PUT --input -`, target);
        });
      }
    }
  } else {
    check('Remote not set', false, 'No GitHub remote found');
  }

  // Summary
  const passed = results.filter(r => r.pass).length;
  const failed = results.filter(r => !r.pass).length;
  console.log(`\n ${passed} passed, ${failed} failed`);
  if (failed > 0 && !fix) console.log(' Run: mekong audit . --fix');
}

// --military flag: delegate to patrol script
if (process.argv.includes('--military')) {
  console.log('\n🔍 Running military camp patrol...');
  require(path.join(MEKONG_ROOT, 'scripts/patrol.cjs'));
}

main();
