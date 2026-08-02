#!/usr/bin/env node
/**
 * mekong bootstrap — CK init harness for mekong-cli
 * Unifies config roots, self-heals, generates project scaffolds.
 * @module bootstrap
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '../..');
const CLAUDE_DIR = path.join(ROOT, '.claude');

function log(tag, msg) { console.log(`[${tag}] ${msg}`); }

function run(cmd) {
  try { execSync(cmd, { cwd: ROOT, stdio: 'pipe' }).toString().trim(); }
  catch(e) { return ''; }
}

const HOOKS_SRC = path.join(ROOT, 'mekong/hooks');
const GLOBAL_HOOKS = path.join(os.homedir(), '.claude/hooks');

function checkHealth() {
  const issues = [];
  if (!fs.existsSync(CLAUDE_DIR)) issues.push('Missing .claude/');
  if (!fs.existsSync(path.join(CLAUDE_DIR, 'settings.json'))) issues.push('Missing settings.json');
  if (!fs.existsSync(path.join(ROOT, '.ck.json'))) issues.push('Missing .ck.json');

  // Check canonical hook source (mekong/hooks/)
  const mekongHooks = fs.existsSync(HOOKS_SRC) ? fs.readdirSync(HOOKS_SRC).filter(f => f.endsWith('.cjs')) : [];
  if (mekongHooks.length === 0) issues.push('Missing hook files in mekong/hooks/');
  if (!fs.existsSync(path.join(HOOKS_SRC, 'lib'))) issues.push('Missing mekong/hooks/lib/');
  if (!fs.existsSync(path.join(HOOKS_SRC, '__tests__'))) issues.push('Missing mekong/hooks/__tests__/');

  // Check global symlinks (~/.claude/hooks/)
  let brokenSymlinks = 0;
  if (fs.existsSync(GLOBAL_HOOKS)) {
    for (const f of fs.readdirSync(GLOBAL_HOOKS)) {
      const fp = path.join(GLOBAL_HOOKS, f);
      try {
        if (f.endsWith('.cjs')) {
          const real = fs.realpathSync(fp);
          if (!fs.existsSync(real)) { brokenSymlinks++; }
        }
      } catch { brokenSymlinks++; }
    }
    for (const d of ['lib', '__tests__']) {
      const dp = path.join(GLOBAL_HOOKS, d);
      try {
        const real = fs.realpathSync(dp);
        if (!fs.existsSync(real)) { brokenSymlinks++; }
      } catch { brokenSymlinks++; }
    }
  }
  if (brokenSymlinks > 0) issues.push(`${brokenSymlinks} broken global hook symlink(s) in ~/.claude/hooks/`);

  // Check project-level .claude/hooks/ if it exists
  const projectHooksDir = path.join(CLAUDE_DIR, 'hooks');
  const projectHookCount = fs.existsSync(projectHooksDir) ? fs.readdirSync(projectHooksDir).filter(f => f.endsWith('.cjs')).length : 0;

  return { healthy: issues.length === 0, issues, mekongHookCount: mekongHooks.length, globalHookCount: brokenSymlinks, projectHookCount };
}

function selfInit() {
  log('init', 'Running ck init for mekong-cli...');
  run('npx ck init -g --kit engineer --yes --force');
  log('init', 'CK init complete');
}

function selfHeal() {
  log('heal', 'Checking health...');
  const health = checkHealth();
  if (health.healthy) { log('heal', '✓ Healthy'); return; }
  health.issues.forEach(i => log('heal', `✗ ${i}`));
  selfInit();
}

const cmd = process.argv[2] || 'help';
switch (cmd) {
  case 'init':
    if (process.argv[3] === '--self') {
      const health = checkHealth();
      if (process.argv[4] === '--fix') selfHeal();
      else console.log(JSON.stringify(health, null, 2));
    } else {
      selfInit();
    }
    break;
  case 'particle':
  case 'new':
    {
      const init = require(path.join(ROOT, 'mekong/init/index.cjs'));
      const name = process.argv[3];
      if (name) init.createParticle(name);
      else console.log('Usage: mekong particle <project-name>');
    }
    break;
  case 'audit':
    require(path.join(ROOT, 'mekong/audit/index.cjs'));
    break;
  case 'health':
    console.log(JSON.stringify(checkHealth(), null, 2));
    break;
  case 'help':
  default:
    console.log(`
Usage: mekong [command]

Commands:
  mekong init                   Run CK init
  mekong init --self            Check health
  mekong init --self --fix      Auto-fix
  mekong init <project>         Generate Economic Particle
  mekong particle <name>        Alias for mekong init
  mekong studio init <name>     Generate VC Studio (venture builder)
  mekong audit [path]           Audit project vs Constitution
  mekong audit [path] --fix     Auto-fix audit violations
  mekong health                 Check mekong-cli health
Note: mekong init (particle) != mekong studio init (studio).
  Studio is higher-level, contains many particles.
`);
  }

