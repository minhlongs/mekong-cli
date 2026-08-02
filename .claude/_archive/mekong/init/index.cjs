#!/usr/bin/env node
/**
 * mekong init — Generate Economic Particle scaffold + CK init
 * Usage: mekong init <project-name>
 *
 * Creates a new project with:
 * 1. ZenOS skeleton (ZENOS.md, .github/workflows/)
 * 2. CK init harness (.claude/, hooks, settings, statusLine)
 * 3. Git init
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

const ROOT = path.resolve(__dirname, '../..');
const SKEL = path.join(__dirname, 'skel');

function run(cmd, cwd) {
  try { execSync(cmd, { cwd: cwd || process.cwd(), stdio: 'pipe', encoding: 'utf8' }); }
  catch(e) { /* best effort */ }
}

/**
 * Render template variables in file content.
 * Supports: {{DATE}}, {{NAME}}, {{MISSION}}, {{YEAR}}
 */
function renderVars(content, name) {
  const date = new Date();
  const vars = {
    'DATE': date.toISOString().slice(0, 10),
    'YEAR': String(date.getFullYear()),
    'NAME': name,
    'MISSION': '_',
    'PARTICLE_ID': name.toLowerCase().replace(/[^a-z0-9-]/g, '-'),
    'PARTICLE_NAME': name,
    'MISSION_STATEMENT': '_',
    'TEMPLATE_NAME': 'default'
  };
  let result = content;
  // Replace $(date +%Y-%m-%d) shell pattern
  result = result.replace(/\$\(date\s*\+[^)]+\)/g, vars.DATE);
  // Replace {{VARS}}
  for (const [k, v] of Object.entries(vars)) {
    const re = new RegExp('\\{\\{\\s*' + k + '\\s*\\}\\}', 'g');
    result = result.replace(re, v);
  }
  return result;
}

function copyDir(src, dest, particleName) {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  for (const f of fs.readdirSync(src)) {
    const s = path.join(src, f);
    const d = path.join(dest, f);
    if (fs.statSync(s).isDirectory()) copyDir(s, d, particleName);
    else {
      const content = fs.readFileSync(s, 'utf8');
      const rendered = renderVars(content, particleName || 'project');
      fs.writeFileSync(d, rendered);
    }
  }
}

function installCkInit(target) {
  const claudeDir = path.join(target, '.claude');
  const hooksDir = path.join(claudeDir, 'hooks');
  const libDir = path.join(hooksDir, 'lib');

  console.log('  → Installing CK init harness...');

  // Create .claude/ structure
  fs.mkdirSync(hooksDir, { recursive: true });
  fs.mkdirSync(libDir, { recursive: true });
  fs.mkdirSync(path.join(claudeDir, 'commands'), { recursive: true });
  fs.mkdirSync(path.join(claudeDir, 'agents'), { recursive: true });
  fs.mkdirSync(path.join(claudeDir, 'skills'), { recursive: true });

  // Symlink hooks from global CK init (or mekong canonical source)
  const hookSource = path.join(ROOT, 'mekong/hooks');
  const globalHookSource = path.join(os.homedir(), '.claude/hooks');

  const srcHooks = fs.existsSync(hookSource) ? hookSource :
                   fs.existsSync(globalHookSource) ? globalHookSource : null;

  if (srcHooks) {
    for (const f of fs.readdirSync(srcHooks)) {
      const fp = path.join(srcHooks, f);
      if (f.endsWith('.cjs')) {
        try { fs.symlinkSync(fp, path.join(hooksDir, f)); } catch {}
      }
    }
    // Copy lib files
    const srcLib = path.join(srcHooks, 'lib');
    if (fs.existsSync(srcLib)) {
      for (const f of fs.readdirSync(srcLib)) {
        try { fs.copyFileSync(path.join(srcLib, f), path.join(libDir, f)); } catch {}
      }
    }
  }

  // Create .ck.json
  const ckJson = { version: '2.20.0', kit: 'engineer', env: {} };
  fs.writeFileSync(path.join(target, '.ck.json'), JSON.stringify(ckJson, null, 2));

  // Create minimal settings.json
  const settings = {
    $schema: 'https://json.schemastore.org/claude-code-settings.json',
    env: {},
    hooks: {},
    statusLine: {
      type: 'command',
      command: 'node "$CLAUDE_PROJECT_DIR/.claude/statusline.cjs"',
      padding: 0
    }
  };
  fs.writeFileSync(path.join(claudeDir, 'settings.json'), JSON.stringify(settings, null, 2));

  // Copy statusLine if available
  const statusSrc = path.join(os.homedir(), '.claude', 'statusline.cjs');
  if (fs.existsSync(statusSrc)) {
    try { fs.copyFileSync(statusSrc, path.join(claudeDir, 'statusline.cjs')); } catch {}
  }

  console.log('  → CK init harness installed');
}

/**
 * Create a new Economic Particle.
 * Called by bootstrap (particle/new commands) or directly via CLI.
 * @param {string} name - Project name
 */
function createParticle(name) {
  // Use caller's original dir (me wrapper cd's to mekong-cli, OLDPWD preserves caller)
  const callerDir = process.env.OLDPWD || process.cwd();
  const target = path.resolve(callerDir, name);
  if (fs.existsSync(target)) {
    console.error(`Error: ${name} already exists`);
    process.exit(1);
  }

  console.log(`\n🏗️  Creating Economic Particle: ${name}`);
  fs.mkdirSync(target, { recursive: true });

  // Step 1: Copy skeleton with template rendering
  console.log('  → Copying ZenOS skeleton...');
  copyDir(SKEL, target, name);

  // Step 2: CK init harness
  installCkInit(target);

  // Step 3: Codebase Memory index
  try {
    const { execSync } = require('child_process');
    execSync('command -v codebase-memory-mcp', { stdio: 'pipe' });
    console.log('  → Indexing codebase with Codebase Memory...');
    execSync('codebase-memory-mcp --index . 2>/dev/null', { cwd: target, stdio: 'pipe', timeout: 120000 });
    console.log('  → Codebase indexed');
  } catch (e) {
    // codebase-memory not installed — skip
  }

  // Step 4: Git init
  console.log('  → Initializing git...');
  run('git init', target);
  run('git checkout -b main', target);
  run('git add -A && git commit -m "feat: initial commit — ZenOS Economic Particle"', target);

  console.log(`\n✅ ${name} created — ready to build.`);
  console.log(`   cd ${name}`);
  console.log(`   mekong audit . --fix  (verify ZenOS compliance)`);
}

// CLI entry: mekong init <name>
const name = process.argv[2];
if (!name || name === 'help') {
  console.log(`
Usage: mekong init <project-name>

Creates a new Economic Particle with:
  - ZenOS Constitution (ZENOS.md)
  - CK init harness (.claude/ + hooks + settings)
  - 2-Guard deploy pipeline (.github/workflows/)
  - Git init
  - Ready for mekong audit --fix
`);
} else {
  createParticle(name);
}

// Export for bootstrap (particle/new commands)
module.exports = { createParticle };
