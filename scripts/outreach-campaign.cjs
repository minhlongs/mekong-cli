#!/usr/bin/env node
/**
 * outreach-campaign.cjs — Full outreach pipeline
 * Usage: node scripts/outreach-campaign.cjs --run
 *        node scripts/outreach-campaign.cjs --list
 *        node scripts/outreach-campaign.cjs --send <name>
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const FILE = path.join(os.homedir(), '.mekong', 'pipeline.json');
const STAGES = ['lead', 'contacted', 'negotiating', 'closed'];
const MEKONG = os.homedir() + '/mekong-cli';

function readPipe() { try { return JSON.parse(fs.readFileSync(FILE, 'utf8')); } catch { return []; } }
function savePipe(d) { fs.mkdirSync(path.dirname(FILE), { recursive: true }); fs.writeFileSync(FILE, JSON.stringify(d, null, 2)); }

function ghSearch(query) {
  try {
    const r = execSync('gh search repos ' + query + ' --json name,owner,url,description --limit 15', { encoding: 'utf8', timeout: 15000 });
    return JSON.parse(r);
  } catch (e) {
    console.log('  GitHub search unavailable (account rate-limited). Try again later.');
    return [];
  }
}

const cmd = process.argv[2];

if (cmd === '--run') {
  console.log('\nScanning for prospects...\n');
  const repos = ghSearch("'topic:ai topic:agent stars:>10 pushed:>2026-06-01'");
  if (!repos.length) {
    console.log('  No prospects found. GH search may be rate-limited.\n');
    process.exit(0);
  }
  const pipe = readPipe();
  let added = 0;
  for (const r of repos) {
    if (!pipe.find(p => p.url === r.url)) {
      pipe.push({ name: r.name, owner: r.owner?.login || '?', url: r.url, desc: r.description || '', stage: 'lead', added: new Date().toISOString(), contacted: null });
      added++;
    }
  }
  savePipe(pipe);
  console.log('  Added ' + added + ' new prospects (' + pipe.length + ' total)\n');
  console.log('  Pipeline:');
  STAGES.forEach(s => console.log('    ' + s.padEnd(15) + pipe.filter(p => p.stage === s).length));
} else if (cmd === '--list') {
  const pipe = readPipe();
  if (!pipe.length) { console.log('Pipeline empty. Run --run first.'); process.exit(0); }
  console.log('\nPipeline (' + pipe.length + ' prospects):\n');
  pipe.forEach((p, i) => console.log('  ' + (i+1) + '. ' + p.name + ' (' + p.owner + ') [' + p.stage + ']'));
} else if (cmd === '--send') {
  const name = process.argv[3];
  const pipe = readPipe();
  const p = pipe.find(x => x.name === name);
  if (!p) { console.error('Prospect "' + name + '" not found'); process.exit(1); }
  execSync('node ' + MEKONG + '/scripts/outreach-gen.cjs --prospect "' + p.name + '" --contact "Founder"', { stdio: 'inherit' });
  p.stage = 'contacted';
  p.contacted = new Date().toISOString();
  savePipe(pipe);
  console.log('\n' + p.name + ' moved to contacted');
} else {
  console.log('Usage: node scripts/outreach-campaign.cjs --run|--list|--send <name>');
}
