#!/usr/bin/env node
/**
 * content-gen.cjs — Content generator for Mekong CLI marketing
 * Usage: node scripts/content-gen.cjs --pillar solo-founder --format blog
 */
'use strict';
const fs = require('fs');
const path = require('path');
const yaml = path.join(__dirname, '..', 'config', 'content-pillars.yaml');

const args = process.argv.slice(2);
const pillarFlag = args.indexOf('--pillar');
const formatFlag = args.indexOf('--format');
const pillarName = pillarFlag !== -1 ? args[pillarFlag + 1] : null;
const format = formatFlag !== -1 ? args[formatFlag + 1] : 'blog';

if (!pillarName || args.includes('--help')) {
  console.log('Usage: node scripts/content-gen.cjs --pillar <name> --format blog|twitter|indie-hackers');
  console.log('Pillars: one-person-company, ai-agents, solo-founder-life, binh-phap, zenos');
  process.exit(0);
}

const pillars = {
  'one-person-company': { name: 'One-Person Company', keywords: ['solo founder', 'one-person business', 'micro-saas'] },
  'ai-agents': { name: 'AI Agents in Practice', keywords: ['AI workflow', 'autonomous agents', 'Claude Code'] },
  'solo-founder-life': { name: 'Solo Founder Life', keywords: ['productivity', 'burnout', 'tools'] },
  'binh-phap': { name: 'Binh Phap for Business', keywords: ['strategy', 'competitive analysis'] },
  'zenos': { name: 'ZenOS Philosophy', keywords: ['AI governance', 'constitutional AI', 'OPCOS'] },
};

const pillar = pillars[pillarName];
if (!pillar) { console.error(`Unknown pillar: ${pillarName}`); process.exit(1); }

console.log(`\n📝 Generating ${format} content for "${pillar.name}"...\n`);
console.log(`Topic suggestions:\n`);
const topics = {
  blog: [
    `Why Every Solo Founder Needs an AI Operating System`,
    `How to Replace 5 SaaS Tools with One AI Platform`,
    `The Binh Phap Approach to Business Strategy`,
    `Building a One-Person Billion-Dollar Company`,
    `Constitutional AI: Why Your Business Needs a Constitution`,
  ],
  twitter: [
    `Thread: 5 lessons from building a one-person company OS`,
    `Hot take: AI agents will replace middle management before developers`,
    `Thread: Binh Phap applied to startup strategy 🧵`,
  ],
  indie_hackers: [
    `From $0 to $1M: Building an AI OS for solo founders`,
    `How I replaced my entire team with AI agents`,
  ],
};

const key = format === 'indie-hackers' ? 'indie_hackers' : format;
const suggestions = topics[key] || topics.blog;
suggestions.forEach((t, i) => console.log(`  ${i+1}. ${t}`));

console.log(`\nKeywords: ${pillar.keywords.join(', ')}`);
console.log(`\nTo generate full post: pipe this to an AI agent with the topic.`);
