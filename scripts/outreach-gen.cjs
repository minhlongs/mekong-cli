#!/usr/bin/env node
/**
 * outreach-gen.cjs — Generate consulting outreach email
 * Usage: node scripts/outreach-gen.cjs --prospect "Company name" --contact "CEO name"
 */
'use strict';
const args = process.argv.slice(2);
const prospect = args.includes('--prospect') ? args[args.indexOf('--prospect')+1] : '[Prospect]';
const contact = args.includes('--contact') ? args[args.indexOf('--contact')+1] : '[Contact]';

console.log(`
Subject: AI agents for ${prospect} — build in 1 week

Hi ${contact},

I build AI agents for businesses. Not chatbots — autonomous agents that write code, manage workflows, and automate operations.

Recent example: built an AI video generation platform (Next.js + Stripe + Telegram bot) with 39 AI agents. All autonomous.

What I can do for ${prospect} in 1 week:
- Audit your codebase → find 5 automation opportunities (free)
- Build 1 production-ready AI agent
- Deploy with CI/CD, monitoring, documentation

Pricing:
- AI Agent Audit: $500 (3 days)
- Custom Agent Build: $2,000 (1 week)
- Full Stack (3-5 agents): $5,000 (2 weeks)

Want to start with a free 30-min discovery call?

Best,
[Your name]
Mekong Consulting
`);
