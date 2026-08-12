#!/usr/bin/env node
/**
 * lead-scorer.cjs — Lead scoring engine for Mekong CLI
 * Reads trial data + SQLite ledger → calculates lead score
 * Usage: node scripts/lead-scorer.cjs [--json]
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const SCORES = {
  install: 10,
  trial_started: 20,
  trial_configured: 20,
  first_workflow: 30,
  payment: 50,
  inactive_30d: -20,
};

function calculateScore(user) {
  let score = 0;
  if (user.trialStarted) score += SCORES.trial_started;
  if (user.configured) score += SCORES.trial_configured;
  if (user.firstWorkflowRun) score += SCORES.first_workflow;
  if (user.paid) score += SCORES.payment;
  if (user.inactive30d) score += SCORES.inactive_30d;
  return Math.max(0, score);
}

function determineStage(score, paid) {
  if (paid) return 'paid';
  if (score >= 50) return 'trial';
  if (score >= 20) return 'trial';
  return 'lead';
}

function determineNextAction(score, stage, paid) {
  if (paid) return 'retain';
  if (score >= 40 && score < 50) return 'send_trial_ending_email';
  if (score >= 20 && score < 40) return 'send_onboarding_tips';
  if (score < 20) return 'send_welcome_series';
  return 'monitor';
}

async function main() {
  const trialFile = path.join(os.homedir(), '.mekong', 'trial.json');
  let results = [];

  try {
    const trials = JSON.parse(fs.readFileSync(trialFile, 'utf8'));
    for (const [email, data] of Object.entries(trials)) {
      const daysSinceStart = Math.floor(
        (Date.now() - new Date(data.startedAt).getTime()) / (24 * 60 * 60 * 1000)
      );
      const user = {
        email,
        trialStarted: true,
        configured: data.creditsUsed > 0,
        firstWorkflowRun: data.creditsUsed > 0,
        paid: false, // Would check Stripe subscription status
        inactive30d: daysSinceStart > 30 && !data.expired,
      };
      const score = calculateScore(user);
      const stage = determineStage(score, user.paid);
      const nextAction = determineNextAction(score, stage, user.paid);

      results.push({
        userId: email,
        score,
        stage,
        nextAction,
        daysSinceStart,
      });
    }
  } catch {
    console.log('No trial data found');
    process.exit(0);
  }

  if (process.argv.includes('--json')) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const r of results) {
      console.log(`Lead userId=${r.userId} score=${r.score} stage=${r.stage} nextAction=${r.nextAction}`);
    }
    const totalScore = results.reduce((s, r) => s + r.score, 0);
    const avgScore = results.length > 0 ? totalScore / results.length : 0;
    console.log(`\nSummary: ${results.length} leads, avg score ${avgScore.toFixed(0)}`);
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
