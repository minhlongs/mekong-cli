#!/usr/bin/env node
/**
 * contract-gate.cjs — Contract-Driven Code Gate
 * Kiểm tra file changes có vi phạm scope contract không
 *
 * Usage: node scripts/contract-gate.cjs [--check] [--file <path>]
 *        node scripts/contract-gate.cjs (check all staged files)
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CONTRACT_FILE = path.join(process.cwd(), '.scope-contract.yaml');
const IS_CHECK = process.argv.includes('--check');
const TARGET_FILE = process.argv.indexOf('--file') !== -1 ? process.argv[process.argv.indexOf('--file') + 1] : null;

function loadContract() {
  try {
    const raw = fs.readFileSync(CONTRACT_FILE, 'utf8');
    // Simple YAML parser (basic)
    const lines = raw.split('\n');
    const contract = { agents: {}, default_policy: {} };
    let section = 'default';
    let agentName = null;
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('agents:')) { section = 'agents'; continue; }
      if (section === 'agents' && trimmed.startsWith('  ') && !trimmed.startsWith('    ')) {
        agentName = trimmed.replace(':', '').trim();
        contract.agents[agentName] = { allowed_paths: [], forbidden_paths: [], verify_gates: [] };
        continue;
      }
      if (agentName && trimmed.startsWith('- ')) {
        const val = trimmed.replace('- ', '');
        if (line.includes('allowed_paths')) contract.agents[agentName].allowed_paths.push(val);
        else if (line.includes('forbidden_paths')) contract.agents[agentName].forbidden_paths.push(val);
        else if (line.includes('verify_gates')) contract.agents[agentName].verify_gates.push(val);
      }
    }
    return contract;
  } catch { return { agents: {}, default_policy: {} }; }
}

function checkFile(filePath, contract, agentName) {
  const agent = contract.agents[agentName];
  if (!agent) return { ok: true }; // No contract for this agent

  for (const forbidden of agent.forbidden_paths) {
    const pattern = forbidden.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*');
    if (new RegExp(pattern).test(filePath)) {
      return { ok: false, reason: `File ${filePath} matches forbidden path: ${forbidden}` };
    }
  }

  if (agent.allowed_paths.length > 0) {
    const allowed = agent.allowed_paths.some(p => filePath.startsWith(p));
    if (!allowed) {
      return { ok: false, reason: `File ${filePath} not in allowed paths: ${agent.allowed_paths.join(', ')}` };
    }
  }

  return { ok: true };
}

function main() {
  const contract = loadContract();
  if (!contract.agents || Object.keys(contract.agents).length === 0) {
    console.log('No .scope-contract.yaml found — scope gate skipped');
    process.exit(0);
  }

  let files = [];
  if (TARGET_FILE) {
    files = [TARGET_FILE];
  } else {
    try {
      const staged = execSync('git diff --cached --name-only', { encoding: 'utf8', timeout: 5000 });
      files = staged.trim().split('\n').filter(Boolean);
    } catch { files = []; }
  }

  if (files.length === 0) {
    console.log('No files to check');
    process.exit(0);
  }

  let violations = [];
  for (const file of files) {
    // Detect agent from file path
    const agentMatch = file.match(/AI\/(\w+)\.md/);
    const agentName = agentMatch ? agentMatch[1] : null;
    if (agentName) {
      const result = checkFile(file, contract, agentName);
      if (!result.ok) violations.push(result.reason);
    }
  }

  if (violations.length > 0) {
    console.log('❌ SCOPE CONTRACT VIOLATIONS:');
    violations.forEach(v => console.log(`  - ${v}`));
    process.exit(1);
  } else {
    console.log('✅ Scope contract check passed');
    process.exit(0);
  }
}

main();
