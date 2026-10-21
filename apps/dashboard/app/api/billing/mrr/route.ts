/**
 * Real-time MRR API Route
 * Protected by guardDashboardApiRoute; returns synthetic metrics in pilot demo mode.
 */

import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'
import Stripe from 'stripe'
import { logger } from '@/lib/utils/logger'
import { guardDashboardApiRoute, isDashboardDemoMode } from '@/lib/demo-guard'

export const dynamic = 'force-dynamic'

function getStripe(): Stripe {
  if (!process.env.STRIPE_SECRET_KEY) {
    throw new Error('STRIPE_SECRET_KEY not configured')
  }
  return new Stripe(process.env.STRIPE_SECRET_KEY, {
    apiVersion: '2026-02-25.clover',
  })
}

export interface MRRMetrics {
  mrr: number
  arr: number
  activeSubscriptions: number
  newMRR: number
  churnedMRR: number
  netNewMRR: number
  averageRevenuePerUser: number
  breakdown: { plan: string; count: number; mrr: number }[]
  growth: { month: string; mrr: number }[]
}

const SYNTHETIC_MRR_METRICS: MRRMetrics = {
  mrr: 12450.0,
  arr: 149400.0,
  activeSubscriptions: 127,
  newMRR: 2100.0,
  churnedMRR: 350.0,
  netNewMRR: 1750.0,
  averageRevenuePerUser: 98.03,
  breakdown: [
    { plan: 'Starter (Synthetic)', count: 52, mrr: 2600 },
    { plan: 'Professional (Synthetic)', count: 58, mrr: 5742 },
    { plan: 'Enterprise (Synthetic)', count: 17, mrr: 4108 },
  ],
  growth: [
    { month: 'Aug', mrr: 8450 },
    { month: 'Sep', mrr: 9200 },
    { month: 'Oct', mrr: 10100 },
    { month: 'Nov', mrr: 11200 },
    { month: 'Dec', mrr: 11800 },
    { month: 'Jan', mrr: 12450 },
  ],
}

function toMonthlyAmount(unitAmount: number, interval?: string): number {
  const amount = unitAmount / 100
  if (interval === 'year') return amount / 12
  if (interval === 'week') return amount * 4.33
  if (interval === 'day') return amount * 30
  return amount
}

async function calculateMRR(): Promise<MRRMetrics> {
  const stripe = getStripe()
  const subscriptions = await stripe.subscriptions.list({
    status: 'active',
    limit: 100,
    expand: ['data.items.data.price'],
  })

  let totalMRR = 0
  const planBreakdown: Record<string, { count: number; mrr: number }> = {}

  for (const sub of subscriptions.data) {
    for (const item of sub.items.data) {
      const price = item.price
      const monthlyAmount =
        price.type === 'recurring' && price.unit_amount
          ? toMonthlyAmount(price.unit_amount, price.recurring?.interval)
          : 0
      totalMRR += monthlyAmount
      const planName = price.nickname || price.id
      if (!planBreakdown[planName]) planBreakdown[planName] = { count: 0, mrr: 0 }
      planBreakdown[planName].count++
      planBreakdown[planName].mrr += monthlyAmount
    }
  }

  const startOfMonth = new Date()
  startOfMonth.setDate(1)
  startOfMonth.setHours(0, 0, 0, 0)
  const createdFilter = { gte: Math.floor(startOfMonth.getTime() / 1000) }

  const [newSubs, canceledSubs] = await Promise.all([
    stripe.subscriptions.list({ status: 'active', created: createdFilter, limit: 100 }),
    stripe.subscriptions.list({ status: 'canceled', created: createdFilter, limit: 100 }),
  ])

  let newMRR = 0
  for (const sub of newSubs.data) {
    for (const item of sub.items.data) {
      if (item.price.unit_amount) {
        newMRR += toMonthlyAmount(item.price.unit_amount, item.price.recurring?.interval)
      }
    }
  }

  let churnedMRR = 0
  for (const sub of canceledSubs.data) {
    for (const item of sub.items.data) {
      if (item.price.unit_amount) {
        churnedMRR += toMonthlyAmount(item.price.unit_amount, item.price.recurring?.interval)
      }
    }
  }

  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const currentMonth = new Date().getMonth()
  const growth = Array.from({ length: 6 }, (_, idx) => {
    const i = 5 - idx
    const monthIndex = (currentMonth - i + 12) % 12
    return { month: months[monthIndex], mrr: Math.round(totalMRR * (1 - i * 0.1) * 100) / 100 }
  })

  return {
    mrr: Math.round(totalMRR * 100) / 100,
    arr: Math.round(totalMRR * 12 * 100) / 100,
    activeSubscriptions: subscriptions.data.length,
    newMRR: Math.round(newMRR * 100) / 100,
    churnedMRR: Math.round(churnedMRR * 100) / 100,
    netNewMRR: Math.round((newMRR - churnedMRR) * 100) / 100,
    averageRevenuePerUser:
      subscriptions.data.length > 0 ? Math.round((totalMRR / subscriptions.data.length) * 100) / 100 : 0,
    breakdown: Object.entries(planBreakdown).map(([plan, data]) => ({
      plan,
      count: data.count,
      mrr: Math.round(data.mrr * 100) / 100,
    })),
    growth,
  }
}

export async function GET(request: NextRequest) {
  const blocked = guardDashboardApiRoute(request, { allowSyntheticGet: true })
  if (blocked) return blocked

  if (isDashboardDemoMode()) {
    return NextResponse.json({
      success: true,
      synthetic: true,
      dataSource: 'synthetic-pilot-demo',
      data: SYNTHETIC_MRR_METRICS,
      timestamp: new Date().toISOString(),
    })
  }

  try {
    const metrics = await calculateMRR()
    return NextResponse.json({
      success: true,
      synthetic: false,
      data: metrics,
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    logger.error('MRR API error', error)
    return NextResponse.json({ error: 'Failed to calculate MRR' }, { status: 500 })
  }
}
