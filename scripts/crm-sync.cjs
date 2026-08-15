#!/usr/bin/env node
/**
 * crm-sync.cjs — Sync Mekong CLI users to HubSpot CRM
 * Usage: node scripts/crm-sync.cjs [--sync | --dry-run]
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const HUBSPOT_API_KEY = process.env.HUBSPOT_API_KEY;
const isDryRun = process.argv.includes('--dry-run');
const isSync = process.argv.includes('--sync') || process.argv.includes('--dry-run');

if (!HUBSPOT_API_KEY) {
  console.log('⚠️  HUBSPOT_API_KEY not set. CRM sync skipped.');
  console.log('   Set env var to enable HubSpot integration.');
  console.log('   Get key at: https://app.hubspot.com/ > Settings > Integrations > API Key\n');
  process.exit(0);
}

async function findOrCreateContact(email, properties) {
  if (isDryRun) {
    console.log(`[dry-run] Would create/update contact: ${email}`);
    console.log(`[dry-run] Properties:`, JSON.stringify(properties));
    return { id: 'dry-run' };
  }
  try {
    const hubspot = require('@hubspot/api-client');
    const client = new hubspot.Client({ apiKey: HUBSPOT_API_KEY });
    const response = await client.crm.contacts.basicApi.create({
      properties: {
        email,
        firstname: properties.firstName || '',
        lastname: properties.lastName || '',
        hs_lead_status: properties.stage || 'lead',
        lifecycle_stage: properties.stage === 'paid' ? 'customer' : 'lead',
      },
    });
    console.log(`✅ Contact created/updated: ${email} (ID: ${response.id})`);
    return response;
  } catch (e) {
    console.error(`HubSpot error for ${email}:`, e.message);
    return null;
  }
}

async function updateDealStage(email, stage, amount) {
  if (isDryRun) {
    console.log(`[dry-run] Would update deal: ${email} → stage=${stage} amount=${amount}`);
    return true;
  }
  try {
    const hubspot = require('@hubspot/api-client');
    const client = new hubspot.Client({ apiKey: HUBSPOT_API_KEY });
    await client.crm.deals.basicApi.create({
      properties: {
        dealname: `Mekong CLI - ${email}`,
        dealstage: stage,
        amount: String(amount || 0),
        pipeline: 'Mekong Pipeline',
      },
    });
    console.log(`✅ Deal updated: ${email} → ${stage}`);
    return true;
  } catch (e) {
    console.error(`Deal error for ${email}:`, e.message);
    return false;
  }
}

async function main() {
  console.log(`CRM Sync ${isDryRun ? '(DRY RUN)' : ''}\n`);

  // Read trial data
  const trialFile = path.join(os.homedir(), '.mekong', 'trial.json');
  let users = [];
  try {
    const trials = JSON.parse(fs.readFileSync(trialFile, 'utf8'));
    users = Object.entries(trials).map(([email, data]) => ({
      email, stage: data.expired ? 'churned' : 'trial', data,
    }));
    console.log(`Found ${users.length} users in trial database\n`);
  } catch {
    console.log('No trial data found. Run signup first.\n');
  }

  for (const user of users) {
    await findOrCreateContact(user.email, {
      firstName: user.email.split('@')[0],
      stage: user.stage,
    });
  }

  console.log(`\nCRM sync complete. ${users.length} user(s) processed.`);
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
