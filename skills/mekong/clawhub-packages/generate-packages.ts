/**
 * ClawHub Package Generator
 * Generates publishable package configs for each Mekong department.
 * Run: npx tsx skills/mekong/clawhub-packages/generate-packages.ts
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'fs';
import { join, basename } from 'path';

interface Department {
  slug: string;
  name: string;
  role: string;
  layer: string;
  chapter: string;
  prefixes: string[];
  freeLimit: number;
  description: string;
}

const DEPARTMENTS: Department[] = [
  { slug: 'finance', name: 'Mekong Finance', role: 'CFO', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['accounting', 'finance', 'finops', 'treasury'], freeLimit: 5, description: 'CFO operations — P&L, budgeting, collections, treasury' },
  { slug: 'sales', name: 'Mekong Sales', role: 'CRO', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['sales', 'sdr', 'ae', 'revops'], freeLimit: 5, description: 'CRO operations — pipeline, outreach, deal close, RevOps' },
  { slug: 'marketing', name: 'Mekong Marketing', role: 'CMO', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['marketing', 'growth', 'writer', 'ck-marketing'], freeLimit: 5, description: 'CMO operations — content engine, campaigns, analytics, growth' },
  { slug: 'hr', name: 'Mekong HR', role: 'CHRO', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['hr', 'people', 'recruiter'], freeLimit: 5, description: 'CHRO operations — recruiting, onboarding, performance cycles' },
  { slug: 'legal', name: 'Mekong Legal', role: 'CLO', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['legal', 'compliance', 'governance'], freeLimit: 5, description: 'CLO operations — contract review, compliance, governance' },
  { slug: 'engineering', name: 'Mekong Engineering', role: 'VP Eng', layer: 'engineering', chapter: '軍爭 — Military Contention', prefixes: ['eng', 'engineering', 'dev', 'junior', 'backend', 'frontend', 'tech'], freeLimit: 8, description: 'VP Eng operations — sprints, tech debt, code review, onboarding' },
  { slug: 'devops', name: 'Mekong DevOps', role: 'SRE Lead', layer: 'ops', chapter: '九變 — Nine Variations', prefixes: ['devops', 'sre', 'releng', 'platform', 'infra', 'worker', 'release'], freeLimit: 5, description: 'SRE operations — deploy pipelines, monitoring, incident response' },
  { slug: 'data', name: 'Mekong Data', role: 'CDO', layer: 'engineering', chapter: '軍爭 — Military Contention', prefixes: ['data', 'ml', 'cdp'], freeLimit: 5, description: 'CDO operations — data pipelines, ML ops, CDP, analytics' },
  { slug: 'security', name: 'Mekong Security', role: 'CISO', layer: 'ops', chapter: '九變 — Nine Variations', prefixes: ['sec', 'iam'], freeLimit: 5, description: 'CISO operations — audits, pentest, IAM, incident response' },
  { slug: 'product', name: 'Mekong Product', role: 'CPO', layer: 'product', chapter: '謀攻 — Attack by Stratagem', prefixes: ['product', 'pm', 'design', 'ui', 'ux'], freeLimit: 5, description: 'CPO operations — roadmap, sprints, OKRs, user research' },
  { slug: 'ops', name: 'Mekong Ops', role: 'COO', layer: 'ops', chapter: '九變 — Nine Variations', prefixes: ['ops', 'incident', 'obs'], freeLimit: 5, description: 'COO operations — health sweep, disaster recovery, observability' },
  { slug: 'business', name: 'Mekong Business', role: 'Business Lead', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['business'], freeLimit: 5, description: 'Business operations — revenue engine, quarterly review, hiring' },
  { slug: 'founder', name: 'Mekong Founder', role: 'CEO/Founder', layer: 'founder', chapter: '始計 — Initial Calculations', prefixes: ['founder'], freeLimit: 3, description: 'Founder operations — fundraising, validation, launch, negotiate' },
  { slug: 'studio', name: 'Mekong Studio', role: 'Managing Partner', layer: 'studio', chapter: '孫子兵法 — Complete Art of War', prefixes: ['studio', 'portfolio', 'dealflow', 'venture', 'expert', 'match'], freeLimit: 3, description: 'VC Studio — portfolio management, deal flow, expert matching' },
  { slug: 'ipo', name: 'Mekong IPO', role: 'Pre-IPO Lead', layer: 'founder', chapter: '始計 — Initial Calculations', prefixes: ['ipo', 'ir'], freeLimit: 2, description: 'Pre-IPO operations — readiness check, investor relations, S-1' },
  { slug: 'corpdev', name: 'Mekong CorpDev', role: 'Corp Dev Lead', layer: 'founder', chapter: '始計 — Initial Calculations', prefixes: ['corpdev'], freeLimit: 3, description: 'Corp Dev — M&A evaluation, integration, synergy analysis' },
  { slug: 'intl', name: 'Mekong International', role: 'Intl Lead', layer: 'business', chapter: '作戰 — Waging War', prefixes: ['intl'], freeLimit: 3, description: 'International operations — market assessment, localization, compliance' },
  { slug: 'esg', name: 'Mekong ESG', role: 'ESG Officer', layer: 'ops', chapter: '九變 — Nine Variations', prefixes: ['esg'], freeLimit: 3, description: 'ESG operations — carbon tracking, DEI, governance reporting' },
  { slug: 'risk', name: 'Mekong Risk', role: 'CRO (Risk)', layer: 'ops', chapter: '九變 — Nine Variations', prefixes: ['risk'], freeLimit: 3, description: 'Risk operations — assessment, fraud detection, monitoring' },
  { slug: 'audit', name: 'Mekong Audit', role: 'Internal Audit', layer: 'ops', chapter: '九變 — Nine Variations', prefixes: ['audit'], freeLimit: 3, description: 'Audit operations — SOX, ITGC, execution, compliance' },
  { slug: 'board', name: 'Mekong Board', role: 'Board Secretary', layer: 'founder', chapter: '始計 — Initial Calculations', prefixes: ['board'], freeLimit: 2, description: 'Board operations — minutes, compliance, management' },
  { slug: 'intel', name: 'Mekong Intelligence', role: 'AGO', layer: 'studio', chapter: '孫子兵法 — Complete Art of War', prefixes: ['intel', 'terrain', 'momentum'], freeLimit: 3, description: 'Strategic intelligence — terrain analysis, momentum, blind spots' },
];

function getCommandsForDepartment(dept: Department, allCommands: string[]): string[] {
  return allCommands.filter(cmd =>
    dept.prefixes.some(prefix => cmd === prefix || cmd.startsWith(`${prefix}-`))
  );
}

function generatePackageConfig(dept: Department, commands: string[]) {
  return {
    name: `mekong-${dept.slug}`,
    version: '1.0.0',
    description: dept.description,
    author: 'Binh Phap Venture Studio',
    license: 'BSL-1.1',
    role: dept.role,
    layer: dept.layer,
    chapter: dept.chapter,
    openclaw: '>=2026.3.24',
    commands: {
      free: commands.slice(0, dept.freeLimit),
      paid: commands.slice(dept.freeLimit),
      total: commands.length,
    },
    pricing: {
      free: `${dept.freeLimit} commands`,
      starter: '$49/mo — full department',
      pro: '$149/mo — 3 departments',
      enterprise: '$499/mo — all 22 departments',
    },
    clawhub: {
      category: dept.layer === 'studio' || dept.layer === 'founder' ? 'Strategy' : dept.layer === 'business' ? 'Business Operations' : 'Technical Operations',
      tags: [dept.slug, dept.role.toLowerCase(), dept.layer, 'mekong', 'ai-company-os'],
      install: `clawhub install mekong-${dept.slug}`,
    },
  };
}

// Main
const commandsDir = join(process.cwd(), '.claude', 'commands');
const allCommands = readdirSync(commandsDir)
  .filter(f => f.endsWith('.md'))
  .map(f => basename(f, '.md'))
  .sort();

const outDir = join(process.cwd(), 'skills', 'mekong', 'clawhub-packages');
mkdirSync(outDir, { recursive: true });

const summary: Record<string, { total: number; free: number; paid: number }> = {};

for (const dept of DEPARTMENTS) {
  const commands = getCommandsForDepartment(dept, allCommands);
  const config = generatePackageConfig(dept, commands);
  const outFile = join(outDir, `mekong-${dept.slug}.json`);
  writeFileSync(outFile, JSON.stringify(config, null, 2) + '\n');
  summary[dept.slug] = { total: commands.length, free: Math.min(dept.freeLimit, commands.length), paid: Math.max(0, commands.length - dept.freeLimit) };
}

// Write summary index
const index = {
  generated: new Date().toISOString(),
  totalDepartments: DEPARTMENTS.length,
  totalCommands: allCommands.length,
  departments: summary,
};
writeFileSync(join(outDir, 'index.json'), JSON.stringify(index, null, 2) + '\n');

console.log(`Generated ${DEPARTMENTS.length} ClawHub packages from ${allCommands.length} commands`);
console.table(summary);
