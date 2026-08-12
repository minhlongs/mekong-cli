#!/usr/bin/env node
/**
 * find-prospects.cjs — Quét GitHub tìm startup tiềm năng cho Mekong Consulting
 *
 * Tiêu chí:
 * - Repo có AI agent / automation / workflow
 * - Active trong 30 ngày
 * - Có ít nhất 10 sao (có budget)
 *
 * Usage: node scripts/find-prospects.cjs [--industry ai|saas|ecom] [--output csv]
 */
'use strict';
const { execSync } = require('child_process');

const QUERIES = {
  ai: 'topic:ai topic:agent stars:\>10 pushed:\>2026-06-01',
  saas: 'topic:saas topic:automation stars:\>20 pushed:\>2026-06-01',
  ecom: 'topic:e-commerce topic:automation stars:\>10 pushed:\>2026-06-01',
};

const industry = process.argv.find(a => a.startsWith('--industry='))?.split('=')[1] || 'ai';
const output = process.argv.includes('--output') ? process.argv[process.argv.indexOf('--output') + 1] : 'text';
const query = QUERIES[industry] || QUERIES.ai;

try {
  const raw = execSync(`gh search repos '${query}' --json name,owner,url,description --limit 20 2>/dev/null`, { encoding: 'utf8', timeout: 15000 });
  const repos = JSON.parse(raw);

  if (output === 'csv') {
    console.log('name,owner,url,stars,description');
    repos.forEach(r => console.log(`${r.name},${r.owner?.login || '?'},${r.url},${"N/A"},"${(r.description || '').replace(/"/g, '""')}"`));
  } else {
    console.log(`\n🔍 Prospects for Mekong Consulting (${repos.length} found)\n`);
    repos.forEach((r, i) => {
      console.log(`${i+1}. ${r.name} (${r.owner?.login || '?'})`);
      console.log(`   ${r.url}`);
      console.log(`   ⭐ ${"N/A"} — ${r.description || 'no description'}`);
      console.log(`   📧 Contact: https://github.com/${r.owner?.login || '?'}`);
      console.log('');
    });
    console.log(`\nRun: node scripts/outreach-gen.cjs --prospect "<name>" --contact "Founder"`);
    console.log(`Export: node scripts/find-prospects.cjs --output csv > prospects.csv`);
  }
} catch (e) {
  console.error('Search failed:', e.message);
  console.log('Make sure gh CLI is authenticated: gh auth status');
}
