#!/usr/bin/env node
/**
 * trial-manager.cjs — 14-day trial credit management for Mekong CLI
 * Usage: node scripts/trial-manager.cjs start <email>
 *        node scripts/trial-manager.cjs status <email>
 *        node scripts/trial-manager.cjs expire <email> (force expire)
 */
'use strict';
const fs = require('fs');
const path = require('path');

const TRIAL_DIR = path.join(require('os').homedir(), '.mekong');
const TRIAL_FILE = path.join(TRIAL_DIR, 'trial.json');
const TRIAL_CREDITS = 50;
const TRIAL_DAYS = 14;
const WARNING_THRESHOLD = 10;

function ensureDir() {
  if (!fs.existsSync(TRIAL_DIR)) fs.mkdirSync(TRIAL_DIR, { recursive: true });
}

function readTrials() {
  try { return JSON.parse(fs.readFileSync(TRIAL_FILE, 'utf8')); }
  catch { return {}; }
}

function writeTrials(data) {
  fs.writeFileSync(TRIAL_FILE, JSON.stringify(data, null, 2));
}

function startTrial(email) {
  ensureDir();
  const trials = readTrials();
  if (trials[email] && !trials[email].expired) {
    console.log(`Trial already active for ${email}. Expires: ${trials[email].expiresAt}`);
    return trials[email];
  }
  const now = new Date();
  const expiresAt = new Date(now.getTime() + TRIAL_DAYS * 24 * 60 * 60 * 1000);
  trials[email] = {
    email,
    credits: TRIAL_CREDITS,
    creditsUsed: 0,
    startedAt: now.toISOString(),
    expiresAt: expiresAt.toISOString(),
    expired: false,
  };
  writeTrials(trials);
  console.log(`✅ Trial started for ${email}. ${TRIAL_CREDITS} MCU credits. Expires: ${expiresAt.toISOString().slice(0,10)}`);
  return trials[email];
}

function getTrialStatus(email) {
  const trials = readTrials();
  const t = trials[email];
  if (!t) return { active: false, reason: 'no_trial' };
  const now = new Date();
  const expires = new Date(t.expiresAt);
  if (now > expires && !t.expired) {
    t.expired = true;
    t.credits = 0;
    writeTrials(trials);
  }
  const remaining = t.credits - (t.creditsUsed || 0);
  return {
    active: !t.expired && remaining > 0,
    email: t.email,
    remainingCredits: Math.max(0, remaining),
    usedCredits: t.creditsUsed || 0,
    expiresAt: t.expiresAt,
    daysLeft: Math.max(0, Math.ceil((expires - now) / (24 * 60 * 60 * 1000))),
    warning: remaining <= WARNING_THRESHOLD && remaining > 0,
    expired: t.expired,
  };
}

function useCredit(email) {
  const trials = readTrials();
  const t = trials[email];
  if (!t) return { success: false, reason: 'no_trial' };
  const status = getTrialStatus(email);
  if (!status.active) return { success: false, reason: status.expired ? 'expired' : 'no_credits' };
  t.creditsUsed = (t.creditsUsed || 0) + 1;
  writeTrials(trials);
  const remaining = t.credits - t.creditsUsed;
  return { success: true, remainingCredits: remaining, warning: remaining <= WARNING_THRESHOLD };
}

// CLI
const cmd = process.argv[2];
const email = process.argv[3];

if (!cmd || cmd === 'help') {
  console.log(`Usage:
  node scripts/trial-manager.cjs start <email>    Start 14-day trial
  node scripts/trial-manager.cjs status <email>   Check trial status
  node scripts/trial-manager.cjs use <email>      Use one credit
  node scripts/trial-manager.cjs expire <email>   Force expire trial`);
  process.exit(0);
}

if (!email) { console.error('Email required'); process.exit(1); }

switch (cmd) {
  case 'start': startTrial(email); break;
  case 'status':
    const s = getTrialStatus(email);
    if (s.active) {
      console.log(`Trial active: ${s.remainingCredits}/${s.remainingCredits + s.usedCredits} credits (${s.daysLeft} days left)`);
      if (s.warning) console.log('⚠️  Low credits — subscribe to keep access');
    } else {
      console.log(`Trial ${s.expired ? 'expired' : 'inactive'}. Run /subscribe to continue.`);
    }
    break;
  case 'use':
    const r = useCredit(email);
    if (r.success) console.log(`Credit used. ${r.remainingCredits} remaining.`);
    else console.log(`Failed: ${r.reason}`);
    break;
  case 'expire':
    const trials = readTrials();
    if (trials[email]) { trials[email].expired = true; trials[email].credits = 0; writeTrials(trials); console.log(`Trial expired for ${email}`); }
    else console.log(`No trial found for ${email}`);
    break;
  default: console.error('Unknown command'); process.exit(1);
}
