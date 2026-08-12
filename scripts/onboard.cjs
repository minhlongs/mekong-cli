#!/usr/bin/env node
/**
 * onboard.cjs — CLI onboarding flow for Mekong CLI
 * Usage: node scripts/onboard.cjs --check
 *        node scripts/onboard.cjs --step 1
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const FILE = path.join(os.homedir(), '.mekong', 'onboard.json');
const STEPS = [
  { id: 1, name: 'Set API Keys', cmd: 'export ANTHROPIC_API_KEY=sk-...' },
  { id: 2, name: 'Choose Agents', cmd: '/agents --list' },
  { id: 3, name: 'Run First Workflow', cmd: '/cook "analyze my idea"' },
  { id: 4, name: 'View Results', cmd: '/status' },
  { id: 5, name: 'Subscribe', cmd: '/subscribe --tier starter' },
];

function readProgress() {
  try { return JSON.parse(fs.readFileSync(FILE, 'utf8')); }
  catch { return { completedSteps: [], startedAt: new Date().toISOString() }; }
}

function saveProgress(data) {
  fs.mkdirSync(path.dirname(FILE), { recursive: true });
  fs.writeFileSync(FILE, JSON.stringify(data, null, 2));
}

const arg = process.argv[2];
if (arg === '--check') {
  const p = readProgress();
  console.log(`\n📋 Onboarding Progress\n`);
  for (const step of STEPS) {
    const done = p.completedSteps.includes(step.id);
    console.log(`  ${done ? '✅' : '⬜'} Step ${step.id}: ${step.name}`);
    if (!done) { console.log(`     Run: ${step.cmd}`); break; }
  }
  const pct = Math.round((p.completedSteps.length / STEPS.length) * 100);
  console.log(`\n  Progress: ${p.completedSteps.length}/${STEPS.length} (${pct}%)`);
} else if (arg === '--step') {
  const stepId = parseInt(process.argv[3], 10);
  const step = STEPS.find(s => s.id === stepId);
  if (!step) { console.error(`Invalid step: ${stepId}`); process.exit(1); }
  const p = readProgress();
  if (!p.completedSteps.includes(stepId)) {
    p.completedSteps.push(stepId);
    saveProgress(p);
  }
  console.log(`✅ Step ${stepId} "${step.name}" completed!`);
  if (stepId < STEPS.length) {
    const next = STEPS.find(s => s.id === stepId + 1);
    console.log(`Next: ${next.name} — ${next.cmd}`);
  } else {
    console.log(`🎉 All steps done! Run /subscribe --tier starter`);
  }
} else {
  console.log(`Usage:
  node scripts/onboard.cjs --check       # Show progress
  node scripts/onboard.cjs --step <N>    # Mark step complete`);
}
