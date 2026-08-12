#!/usr/bin/env node
/**
 * zenos-proposal.cjs — ZenOS Commons proposal and voting system
 * Usage: node scripts/zenos-proposal.cjs submit "Title" "Desc" --type soft|operational|foundational
 *        node scripts/zenos-proposal.cjs list [--status pending|active|passed|rejected]
 *        node scripts/zenos-proposal.cjs vote <id> yes|no|abstain
 *        node scripts/zenos-proposal.cjs status <id>
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const DATA_DIR = path.join(os.homedir(), '.mekong', 'commons');
const PROPOSALS_FILE = path.join(DATA_DIR, 'proposals.json');

const THRESHOLDS = {
  soft: { pct: 0.50, quorum: 3, label: 'Simple majority' },
  operational: { pct: 0.66, quorum: 5, label: '2/3 supermajority' },
  foundational: { pct: 0.75, quorum: 7, label: '3/4 supermajority' },
};

function ensureDir() { if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true }); }

function readProposals() {
  ensureDir();
  try { return JSON.parse(fs.readFileSync(PROPOSALS_FILE, 'utf8')); }
  catch { return []; }
}

function writeProposals(data) {
  fs.writeFileSync(PROPOSALS_FILE, JSON.stringify(data, null, 2));
}

function submit(title, description, type) {
  if (!THRESHOLDS[type]) { console.error(`Invalid type: ${type}. Use: soft, operational, foundational`); process.exit(1); }
  const proposals = readProposals();
  const now = new Date();
  const proposal = {
    id: crypto.randomUUID().slice(0, 8),
    title, description, type,
    status: 'active',
    author: process.env.USER || 'unknown',
    createdAt: now.toISOString(),
    votingEndsAt: new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    votes: { yes: 0, no: 0, abstain: 0 },
    voters: [],
    result: null,
  };
  proposals.push(proposal);
  writeProposals(proposals);
  console.log(`📝 Proposal submitted: #${proposal.id} "${title}"`);
  console.log(`   Type: ${type} | Voting ends: ${proposal.votingEndsAt.slice(0, 10)}`);
  return proposal.id;
}

function listProposals(statusFilter) {
  const proposals = readProposals();
  const filtered = statusFilter ? proposals.filter(p => p.status === statusFilter) : proposals;
  if (filtered.length === 0) { console.log('No proposals found.'); return; }
  console.log(`Proposals (${filtered.length}):\n`);
  for (const p of filtered) {
    const total = p.votes.yes + p.votes.no + p.votes.abstain;
    console.log(`  #${p.id.padEnd(8)} [${p.status.padEnd(10)}] ${p.title.padEnd(40)} (${total} votes)`);
  }
}

function vote(proposalId, choice) {
  if (!['yes', 'no', 'abstain'].includes(choice)) {
    console.error('Vote must be: yes, no, or abstain'); process.exit(1);
  }
  const proposals = readProposals();
  const p = proposals.find(p => p.id === proposalId);
  if (!p) { console.error(`Proposal #${proposalId} not found.`); process.exit(1); }
  if (p.status !== 'active') { console.error(`Proposal #${proposalId} is ${p.status}, not active.`); process.exit(1); }
  if (new Date() > new Date(p.votingEndsAt)) {
    p.status = 'expired';
    writeProposals(proposals);
    console.error('Voting period ended.'); process.exit(1);
  }

  const voter = process.env.USER || 'unknown';
  if (p.voters.includes(voter)) { console.error('Already voted.'); process.exit(1); }

  p.votes[choice]++;
  p.voters.push(voter);
  writeProposals(proposals);
  console.log(`🗳️  Vote recorded: #${proposalId} — ${choice}`);
}

function status(proposalId) {
  const proposals = readProposals();
  const p = proposals.find(p => p.id === proposalId);
  if (!p) { console.error(`Proposal #${proposalId} not found.`); process.exit(1); }
  const total = p.votes.yes + p.votes.no + p.votes.abstain;
  const yesPct = total > 0 ? (p.votes.yes / (total - p.votes.abstain)) * 100 : 0;
  const threshold = THRESHOLDS[p.type];

  console.log(`\n📋 Proposal #${p.id}: ${p.title}`);
  console.log(`   Type: ${p.type} (${threshold.label})`);
  console.log(`   Status: ${p.status}`);
  console.log(`   Author: ${p.author}`);
  console.log(`   Created: ${p.createdAt.slice(0, 10)}`);
  console.log(`   Voting ends: ${p.votingEndsAt.slice(0, 10)}`);
  console.log(`\n   Votes: ${p.votes.yes} yes / ${p.votes.no} no / ${p.votes.abstain} abstain (${total} total)`);
  if (total - p.votes.abstain > 0) {
    console.log(`   Yes %: ${yesPct.toFixed(1)}% (need ${threshold.pct * 100}%)`);
    console.log(`   Quorum: ${total}/${threshold.quorum}`);
    console.log(`   Result: ${yesPct >= threshold.pct * 100 && total >= threshold.quorum ? '✅ PASS' : '⏳ PENDING'}`);
  }

  // Auto-resolve if ended
  if (p.status === 'active' && new Date() > new Date(p.votingEndsAt)) {
    const passed = yesPct >= threshold.pct * 100 && total >= threshold.quorum && (total - p.votes.abstain) > 0;
    p.status = passed ? 'passed' : 'rejected';
    p.result = passed ? 'passed' : 'rejected';
    writeProposals(proposals);
    console.log(`\n   📢 AUTO-RESOLVED: ${p.status.toUpperCase()}`);
  }
}

const cmd = process.argv[2];
switch (cmd) {
  case 'submit': {
    const typeFlag = process.argv.indexOf('--type');
    const type = typeFlag !== -1 ? process.argv[typeFlag + 1] : 'soft';
    submit(process.argv[3] || 'Untitled', process.argv[4] || '', type);
    break;
  }
  case 'list': {
    const statusFlag = process.argv.indexOf('--status');
    const filter = statusFlag !== -1 ? process.argv[statusFlag + 1] : null;
    listProposals(filter);
    break;
  }
  case 'vote': vote(process.argv[3], process.argv[4]); break;
  case 'status': status(process.argv[3]); break;
  default:
    console.log(`Usage:
  node scripts/zenos-proposal.cjs submit "Title" "Description" --type soft|operational|foundational
  node scripts/zenos-proposal.cjs list [--status pending|active|passed|rejected]
  node scripts/zenos-proposal.cjs vote <id> yes|no|abstain
  node scripts/zenos-proposal.cjs status <id>`);
}
