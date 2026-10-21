/**
 * Subscription Manager for AgencyOS
 * Handles plan management, upgrades, and billing status
 */

import { createClient } from '@supabase/supabase-js'
import type { PricingTier } from './stripe'
import {
  PRICING_TIERS,
  cancelSubscription,
  createCheckoutSession,
  updateSubscription,
} from './stripe'
import type { Subscription, SubscriptionRow, UsageLimits } from './subscription-tiers'
import {
  buildUsageLimits,
  getProjectCountWithClient,
  getTeamMemberCountWithClient,
  mapToSubscription,
} from './subscription-tiers'

export * from './subscription-tiers'

export class SubscriptionManager {
  private supabase

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
  }

  async getSubscription(tenantId: string): Promise<Subscription | null> {
    const { data, error } = await this.supabase
      .from('subscriptions')
      .select('*')
      .eq('tenant_id', tenantId)
      .single()

    if (error || !data) return null
    return this.mapToSubscription(data)
  }

  async getOrCreateSubscription(tenantId: string): Promise<Subscription> {
    let subscription = await this.getSubscription(tenantId)

    if (!subscription) {
      const { data, error } = await this.supabase
        .from('subscriptions')
        .insert({
          tenant_id: tenantId,
          plan: 'FREE',
          status: 'active',
          current_period_start: new Date().toISOString(),
          current_period_end: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
        })
        .select()
        .single()

      if (error) throw new Error(`Failed to create subscription: ${error.message}`)
      subscription = this.mapToSubscription(data)
    }

    return subscription
  }

  async initiateUpgrade(
    tenantId: string,
    targetPlan: PricingTier,
    email: string,
    successUrl: string,
    cancelUrl: string
  ) {
    const tier = PRICING_TIERS[targetPlan]
    if (tier.price === 0) throw new Error('Cannot upgrade to free tier')
    if (!tier.stripePriceId) throw new Error(`No Stripe price configured for ${targetPlan}`)

    return createCheckoutSession({
      customerEmail: email,
      priceId: tier.stripePriceId,
      tenantId,
      successUrl,
      cancelUrl,
    })
  }

  async activateSubscription(
    tenantId: string,
    stripeCustomerId: string,
    stripeSubscriptionId: string,
    plan: PricingTier
  ) {
    const { error } = await this.supabase
      .from('subscriptions')
      .update({
        stripe_customer_id: stripeCustomerId,
        stripe_subscription_id: stripeSubscriptionId,
        plan,
        status: 'active',
        updated_at: new Date().toISOString(),
      })
      .eq('tenant_id', tenantId)

    if (error) throw new Error(`Failed to activate subscription: ${error.message}`)
  }

  async cancelSubscription(tenantId: string) {
    const subscription = await this.getSubscription(tenantId)
    if (!subscription?.stripeSubscriptionId) {
      throw new Error('No active subscription to cancel')
    }

    await cancelSubscription(subscription.stripeSubscriptionId)
    await this.supabase
      .from('subscriptions')
      .update({ cancel_at_period_end: true, updated_at: new Date().toISOString() })
      .eq('tenant_id', tenantId)
  }

  async changePlan(tenantId: string, newPlan: PricingTier) {
    const subscription = await this.getSubscription(tenantId)
    if (!subscription?.stripeSubscriptionId) {
      throw new Error('No active subscription')
    }

    const tier = PRICING_TIERS[newPlan]
    const priceId = 'stripePriceId' in tier ? tier.stripePriceId : undefined
    if (!priceId) throw new Error(`No Stripe price for ${newPlan}`)

    await updateSubscription(subscription.stripeSubscriptionId, priceId)
    await this.supabase
      .from('subscriptions')
      .update({ plan: newPlan, updated_at: new Date().toISOString() })
      .eq('tenant_id', tenantId)
  }

  async getUsageLimits(tenantId: string): Promise<UsageLimits> {
    const subscription = await this.getOrCreateSubscription(tenantId)
    const [teamCount, projectCount] = await Promise.all([
      this.getTeamMemberCount(tenantId),
      this.getProjectCount(tenantId),
    ])

    return buildUsageLimits(subscription.plan, teamCount, projectCount)
  }

  async checkLimit(tenantId: string, resource: keyof UsageLimits): Promise<boolean> {
    const usage = await this.getUsageLimits(tenantId)
    const limit = usage[resource].limit
    if (limit === -1) return true
    return usage[resource].used < limit
  }

  private async getTeamMemberCount(tenantId: string): Promise<number> {
    return getTeamMemberCountWithClient(this.supabase, tenantId)
  }

  private async getProjectCount(tenantId: string): Promise<number> {
    return getProjectCountWithClient(this.supabase, tenantId)
  }

  private mapToSubscription(data: SubscriptionRow): Subscription {
    return mapToSubscription(data)
  }
}

export const subscriptionManager = new SubscriptionManager()
