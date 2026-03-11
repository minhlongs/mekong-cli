import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_dummy', {
  apiVersion: '2025-02-24.acacia',
  typescript: true,
});

export const STRIPE_PRICES = {
  PRO: process.env.STRIPE_PRO_PRICE_ID!,
  ENTERPRISE: process.env.STRIPE_ENTERPRISE_PRICE_ID!,
};

export function getStripe(): Stripe {
  return stripe;
}
