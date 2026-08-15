#!/usr/bin/env node
/**
 * feedback.cjs — Feedback collector (NPS, bugs, feature requests)
 * Usage: node scripts/feedback.cjs --nps
 *        node scripts/feedback.cjs --bug "description"
 *        node scripts/feedback.cjs --report
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const FILE = path.join(os.homedir(), '.mekong', 'feedback.json');

function readFeedback() {
  try { return JSON.parse(fs.readFileSync(FILE, 'utf8')); }
  catch { return { nps: [], bugs: [], features: [] }; }
}

function saveFeedback(data) {
  fs.mkdirSync(path.dirname(FILE), { recursive: true });
  fs.writeFileSync(FILE, JSON.stringify(data, null, 2));
}

const args = process.argv.slice(2);

if (args.includes('--nps')) {
  const scoreIdx = args.indexOf('--nps') + 1;
  const score = parseInt(args[scoreIdx], 10);
  if (isNaN(score) || score < 0 || score > 10) {
    console.log('NPS score (0-10): How likely to recommend Mekong CLI?');
    process.exit(0);
  }
  const data = readFeedback();
  data.nps.push({ score, date: new Date().toISOString() });
  saveFeedback(data);
  const label = score >= 9 ? 'Promoter 🟢' : score >= 7 ? 'Passive 🟡' : 'Detractor 🔴';
  console.log(`✅ NPS recorded: ${score}/10 (${label})`);
} else if (args.includes('--bug')) {
  const idx = args.indexOf('--bug');
  const desc = args.slice(idx + 1).join(' ');
  if (!desc) { console.error('Bug description required'); process.exit(1); }
  const data = readFeedback();
  data.bugs.push({ description: desc, date: new Date().toISOString(), status: 'open' });
  saveFeedback(data);
  console.log(`✅ Bug reported: "${desc}"`);
} else if (args.includes('--report')) {
  const data = readFeedback();
  console.log(`\n📊 Feedback Report\n`);
  console.log(`NPS (${data.nps.length} responses):`);
  const avg = data.nps.length > 0
    ? (data.nps.reduce((s, n) => s + n.score, 0) / data.nps.length).toFixed(1) : 'N/A';
  console.log(`  Average: ${avg}/10`);
  console.log(`  Breakdown:`);
  const promoters = data.nps.filter(n => n.score >= 9).length;
  const detractors = data.nps.filter(n => n.score <= 6).length;
  console.log(`    Promoters: ${promoters}`);
  console.log(`    Detractors: ${detractors}`);
  console.log(`\nBugs (${data.bugs.length}):`);
  const open = data.bugs.filter(b => b.status === 'open').length;
  console.log(`  Open: ${open}`);
  data.bugs.filter(b => b.status === 'open').forEach(b =>
    console.log(`  - ${b.description}`));
  console.log(`\nFeatures (${data.features.length}): pending`);
} else {
  console.log(`Usage:
  node scripts/feedback.cjs --nps 9       # Rate 0-10
  node scripts/feedback.cjs --bug "desc"  # Report bug
  node scripts/feedback.cjs --report      # Show report`);
}
