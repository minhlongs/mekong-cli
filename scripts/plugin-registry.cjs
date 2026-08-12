#!/usr/bin/env node
/**
 * plugin-registry.cjs — Manage local mekong-cli plugin registry
 * Usage: node scripts/plugin-registry.cjs install <path>
 *        node scripts/plugin-registry.cjs list
 *        node scripts/plugin-registry.cjs remove <name>
 *        node scripts/plugin-registry.cjs info <name>
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const ROOT = path.resolve(__dirname, '..');
const PLUGINS_DIR = path.join(ROOT, '.claude', 'plugins');
const REGISTRY_FILE = path.join(PLUGINS_DIR, 'registry.json');

function ensureDir(d) { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); }

function readRegistry() {
  ensureDir(path.dirname(REGISTRY_FILE));
  try { return JSON.parse(fs.readFileSync(REGISTRY_FILE, 'utf8')); }
  catch { return { version: 1, plugins: [] }; }
}

function writeRegistry(data) {
  fs.writeFileSync(REGISTRY_FILE, JSON.stringify(data, null, 2));
}

function installPlugin(srcPath) {
  const manifestPath = path.join(srcPath, '.plugin.json');
  if (!fs.existsSync(manifestPath)) {
    console.error(`No .plugin.json found at ${srcPath}`);
    process.exit(1);
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const name = manifest.name;
  if (!name) { console.error('.plugin.json missing name field'); process.exit(1); }

  const dest = path.join(PLUGINS_DIR, name);
  if (fs.existsSync(dest)) {
    console.error(`Plugin "${name}" already installed. Remove first.`);
    process.exit(1);
  }

  // Copy plugin files
  ensureDir(PLUGINS_DIR);
  fs.cpSync(srcPath, dest, { recursive: true });

  // Create symlinks
  const skillsDir = path.join(ROOT, '.claude', 'skills');
  const commandsDir = path.join(ROOT, '.claude', 'commands');
  ensureDir(skillsDir); ensureDir(commandsDir);

  if (manifest.type === 'skill' || manifest.type === 'both') {
    const skillSrc = path.join(dest, 'SKILL.md');
    if (fs.existsSync(skillSrc)) {
      try { fs.symlinkSync(skillSrc, path.join(skillsDir, `${name}.md`)); } catch {}
    }
  }
  if (manifest.type === 'command' || manifest.type === 'both') {
    const cmdSrc = path.join(dest, 'command.md');
    if (fs.existsSync(cmdSrc)) {
      try { fs.symlinkSync(cmdSrc, path.join(commandsDir, `${name}.md`)); } catch {}
    }
  }

  // Register
  const registry = readRegistry();
  registry.plugins.push({
    name, version: manifest.version, type: manifest.type,
    description: manifest.description,
    installedAt: new Date().toISOString(),
    path: dest,
  });
  writeRegistry(registry);
  console.log(`✅ Plugin "${name}" v${manifest.version} installed`);
}

function listPlugins() {
  const registry = readRegistry();
  if (registry.plugins.length === 0) {
    console.log('No plugins installed.');
    return;
  }
  console.log(`Installed plugins (${registry.plugins.length}):\n`);
  for (const p of registry.plugins) {
    console.log(`  ${p.name.padEnd(20)} v${p.version.padEnd(8)} ${p.type.padEnd(10)} ${p.description || ''}`);
  }
}

function removePlugin(name) {
  const registry = readRegistry();
  const idx = registry.plugins.findIndex(p => p.name === name);
  if (idx === -1) { console.error(`Plugin "${name}" not installed.`); process.exit(1); }

  const dest = path.join(PLUGINS_DIR, name);
  // Remove symlinks
  const skillsDir = path.join(ROOT, '.claude', 'skills');
  const commandsDir = path.join(ROOT, '.claude', 'commands');
  try { fs.unlinkSync(path.join(skillsDir, `${name}.md`)); } catch {}
  try { fs.unlinkSync(path.join(commandsDir, `${name}.md`)); } catch {}
  // Remove directory
  fs.rmSync(dest, { recursive: true, force: true });
  registry.plugins.splice(idx, 1);
  writeRegistry(registry);
  console.log(`✅ Plugin "${name}" removed`);
}

function infoPlugin(name) {
  const registry = readRegistry();
  const p = registry.plugins.find(p => p.name === name);
  if (!p) { console.error(`Plugin "${name}" not installed.`); process.exit(1); }
  console.log(JSON.stringify(p, null, 2));
}

const cmd = process.argv[2];
switch (cmd) {
  case 'install': installPlugin(process.argv[3]); break;
  case 'list': listPlugins(); break;
  case 'remove': removePlugin(process.argv[3]); break;
  case 'info': infoPlugin(process.argv[3]); break;
  default: console.log(`Usage: node scripts/plugin-registry.cjs install|list|remove|info [args]`);
}
