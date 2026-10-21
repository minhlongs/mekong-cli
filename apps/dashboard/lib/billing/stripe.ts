/**
 * Stripe Integration for AgencyOS
 * SEA SaaS Billing Module
 */

import type Stripe from 'stripe'
import type {
  CreateCheckoutParams,
  MRRMetrics,
  PricingTier,
  WebhookEvent,
} from './stripe-types'
import {
  PRICING_TIERS,
  calculateMRRMetrics,
  getStripe,
  handleWebhookEvent,
} from './stripe-types'

export type { CreateCheckoutParams, MRRMetrics, PricingTier, WebhookEvent }
export { PRICING_TIERS, calculateMRRMetrics, getStripe, handleWebhookEvent }

// ═══════════════════════════════════════════════════════════════════════════════
// 💳 CHECKOUT & SUBSCRIPTIONS
// ═══════════════════════════════════════════════════════════════════════════════

export async function createCheckoutSession(params: CreateCheckoutParams) {
  const session = await getStripe().checkout.sessions.create({
    customer: params.customerId,
    customer_email: params.customerId ? undefined : params.customerEmail,
    line_items: [
      {
        price: params.priceId,
        quantity: 1,
      },
    ],
    mode: 'subscription',
    success_url: params.successUrl,
    cancel_url: params.cancelUrl,
    metadata: {
      tenantId: params.tenantId,
    },
    subscription_data: {
      metadata: {
        tenantId: params.tenantId,
      },
    },
    locale: 'auto',
    payment_method_types: ['card'],
    allow_promotion_codes: true,
  })

  return session
}

export async function createCustomer(email: string, name: string, tenantId: string) {
  const customer = await getStripe().customers.create({
    email,
    name,
    metadata: {
      tenantId,
    },
  })

  return customer
}

export async function getSubscription(subscriptionId: string) {
  return getStripe().subscriptions.retrieve(subscriptionId)
}

export async function cancelSubscription(subscriptionId: string) {
  return getStripe().subscriptions.cancel(subscriptionId)
}

export async function updateSubscription(subscriptionId: string, priceId: string) {
  const subscription = await getStripe().subscriptions.retrieve(subscriptionId)

  return getStripe().subscriptions.update(subscriptionId, {
    items: [
      {
        id: subscription.items.data[0].id,
        price: priceId,
      },
    ],
    proration_behavior: 'create_prorations',
  })
}

// ═══════════════════════════════════════════════════════════════════════════════
// 📊 BILLING PORTAL & INVOICES
// ═══════════════════════════════════════════════════════════════════════════════

export async function createBillingPortalSession(customerId: string, returnUrl: string) {
  const session = await getStripe().billingPortal.sessions.create({
    customer: customerId,
    return_url: returnUrl,
  })

  return session
}

export async function getInvoices(customerId: string, limit = 10) {
  const invoices = await getStripe().invoices.list({
    customer: customerId,
    limit,
  })

  return invoices.data
}

export async function getUpcomingInvoice(customerId: string) {
  try {
    const invoices = await getStripe().invoices.list({
      customer: customerId,
      limit: 1,
      status: 'draft',
    })
    return invoices.data[0] || null
  } catch {
    return null
  }
}

export async function constructWebhookEvent(
  payload: string | Buffer,
  signature: string,
  webhookSecret: string
): Promise<Stripe.Event> {
  return getStripe().webhooks.constructEvent(payload, signature, webhookSecret)
}
