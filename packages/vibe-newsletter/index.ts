/**
 * @agencyos/vibe-newsletter — Newsletter & Email Campaign SDK
 *
 * Subscriber lifecycle, segmentation, campaign management, analytics.
 * Reusable across all projects needing email marketing.
 *
 * Usage:
 *   import { createCampaignEngine, createSubscriberManager } from '@agencyos/vibe-newsletter';
 */

// ─── Types ──────────────────────────────────────────────────────

export type SubscriberStatus = 'active' | 'unsubscribed' | 'bounced' | 'complained';
export type CampaignStatus = 'draft' | 'scheduled' | 'sending' | 'sent' | 'cancelled';

export interface Subscriber {
  id: string;
  email: string;
  name?: string;
  status: SubscriberStatus;
  tags: string[];
  subscribedAt: string;
  metadata?: Record<string, string>;
}

export interface Campaign {
  id: string;
  subject: string;
  status: CampaignStatus;
  segmentTags: string[];
  scheduledAt?: string;
  sentAt?: string;
  stats: CampaignStats;
}

export interface CampaignStats {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
}

// ─── Subscriber Manager ─────────────────────────────────────────

export function createSubscriberManager() {
  return {
    /**
     * Segment subscribers by tags
     */
    segmentByTags(subscribers: Subscriber[], requiredTags: string[]): Subscriber[] {
      return subscribers.filter(
        (sub) => sub.status === 'active' && requiredTags.every((tag) => sub.tags.includes(tag)),
      );
    },

    /**
     * Clean list — remove bounced/complained
     */
    cleanList(subscribers: Subscriber[]): { clean: Subscriber[]; removed: number } {
      const clean = subscribers.filter((s) => s.status === 'active');
      return { clean, removed: subscribers.length - clean.length };
    },

    /**
     * Calculate list health score (0-100)
     */
    listHealthScore(subscribers: Subscriber[]): number {
      if (subscribers.length === 0) return 0;
      const active = subscribers.filter((s) => s.status === 'active').length;
      const bounced = subscribers.filter((s) => s.status === 'bounced').length;
      const health = ((active - bounced) / subscribers.length) * 100;
      return Math.max(0, Math.round(health));
    },
  };
}

// ─── Campaign Engine ────────────────────────────────────────────

export function createCampaignEngine() {
  return {
    /**
     * Calculate campaign metrics
     */
    calculateMetrics(stats: CampaignStats): { openRate: number; clickRate: number; bounceRate: number; unsubRate: number } {
      const delivered = stats.delivered || 1;
      return {
        openRate: Math.round((stats.opened / delivered) * 10000) / 100,
        clickRate: Math.round((stats.clicked / delivered) * 10000) / 100,
        bounceRate: Math.round((stats.bounced / stats.sent) * 10000) / 100,
        unsubRate: Math.round((stats.unsubscribed / delivered) * 10000) / 100,
      };
    },

    /**
     * Benchmark campaign performance
     */
    benchmarkPerformance(stats: CampaignStats): { rating: 'excellent' | 'good' | 'average' | 'poor'; insights: string[] } {
      const metrics = this.calculateMetrics(stats);
      const insights: string[] = [];

      if (metrics.openRate > 30) insights.push('Open rate xuất sắc (>30%)');
      else if (metrics.openRate < 15) insights.push('Open rate thấp — cải thiện subject line');

      if (metrics.clickRate > 5) insights.push('Click rate tốt (>5%)');
      else if (metrics.clickRate < 2) insights.push('Click rate thấp — cải thiện CTA');

      if (metrics.bounceRate > 5) insights.push('Bounce rate cao — clean list cần thiết');
      if (metrics.unsubRate > 1) insights.push('Unsub rate cao — review content frequency');

      let rating: 'excellent' | 'good' | 'average' | 'poor' = 'average';
      if (metrics.openRate > 25 && metrics.clickRate > 4) rating = 'excellent';
      else if (metrics.openRate > 20 && metrics.clickRate > 3) rating = 'good';
      else if (metrics.openRate < 10) rating = 'poor';

      return { rating, insights };
    },
  };
}
