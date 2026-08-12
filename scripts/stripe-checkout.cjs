#!/usr/bin/env node
/**
 * stripe-checkout.cjs — Create Stripe Checkout session for Mekong CLI tiers
 * Usage: node scripts/stripe-checkout.cjs --tier starter
 */
'use strict';
const TIERS = {
  starter: { price: 4900, credits: 200, name: 'Starter' },
  growth: { price: 14900, credits: 1000, name: 'Growth' },
  pro: { price: 49900, credits: 5000, name: 'Pro' },
};

const args = process.argv.slice(2);
if (args.includes('--list') || args.length === 0) {
  console.log('Available plans:\n');
  for (const [key, t] of Object.entries(TIERS)) {
    console.log(`  ${key.padEnd(10)} $${t.price/100}/mo  ${t.credits} MCU credits`);
  }
  process.exit(0);
}

const tierFlag = args.indexOf('--tier');
if (tierFlag === -1) {
  console.error('Usage: node scripts/stripe-checkout.cjs --tier starter|growth|pro');
  console.error('       node scripts/stripe-checkout.cjs --list');
  process.exit(1);
}

const tier = args[tierFlag + 1];
const config = TIERS[tier];
if (!config) {
  console.error(`Unknown tier: ${tier}. Options: ${Object.keys(TIERS).join(', ')}`);
  process.exit(1);
}

const secretKey = process.env.STRIPE_SECRET_KEY;
if (!secretKey) {
  console.log(`\n⚠️  STRIPE_SECRET_KEY not set. Would create Checkout session for:\n`);
  console.log(`  Tier: ${config.name} — $${config.price/100}/mo — ${config.credits} MCU credits\n`);
  console.log('Set STRIPE_SECRET_KEY env var to enable live checkout.');
  console.log('Get your key at: https://dashboard.stripe.com/test/apikeys\n');
  process.exit(0);
}

async function main() {
  try {
    const stripe = require('stripe')(secretKey);
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [{ price_data: {
        currency: 'usd',
        product_data: { name: `Mekong CLI ${config.name}` },
        unit_amount: config.price,
        recurring: { interval: 'month' },
      }, quantity: 1 }],
      metadata: { tier, credits: String(config.credits) },
      success_url: 'https://mekongmind.com/success?session_id={CHECKOUT_SESSION_ID}',
      cancel_url: 'https://mekongmind.com/pricing',
    });
    console.log(`\n✅ Checkout session created: ${session.url}\n`);
    console.log(`To open: open "${session.url}"`);
  } catch (err) {
    console.error('Stripe error:', err.message);
    process.exit(1);
  }
}

main();
