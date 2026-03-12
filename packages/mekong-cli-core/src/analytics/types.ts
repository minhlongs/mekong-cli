/**
 * Analytics types for ROIaaS Phase 5 (v0.8).
 * ROI metrics, agent performance, revenue reports, growth indicators.
 */
import type { Timestamp } from '../types/common.js';

/** Time period for analytics aggregation */
export interface AnalyticsPeriod {
  label: string;      // e.g. "2025-03"
  startDate: string;  // ISO
  endDate: string;    // ISO
}

/** ROI calculation result */
export interface ROIMetrics {
  /** Percentage ROI: (value - cost) / cost * 100 */
  roiPercent: number;
  /** Time saved in hours */
  timeSavedHours: number;
  /** Hourly rate used for valuation (USD) */
  hourlyRate: number;
  /** Value from time savings (USD) */
  timeSavedValue: number;
  /** Revenue generated through the platform (USD) */
  revenueGenerated: number;
  /** Total platform cost (USD) */
  totalCost: number;
  /** Net value: timeSavedValue + revenueGenerated - totalCost */
  netValue: number;
  /** Period this covers */
  period: AnalyticsPeriod;
  computedAt: Timestamp;
}

/** Per-agent AGI score (0-100) per HIEN-PHAP Điều 7.3 */
export interface AgentPerformance {
  agentName: string;
  /** Overall 0-100 score */
  agiScore: number;
  /** Component scores (0-100 each) */
  phaseProgressScore: number;    // weight 30%
  activityScore: number;         // weight 25%
  successRateScore: number;      // weight 25%
  resilienceScore: number;       // weight 20%
  /** Raw metrics */
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  successRate: number;           // 0-1
  errorRecoveryRate: number;     // 0-1
  recentCommits: number;         // activity proxy
  phasesCompleted: number;       // of total phases
  totalPhases: number;
  computedAt: Timestamp;
}

/** Revenue aggregation report */
export interface RevenueReport {
  period: AnalyticsPeriod;
  /** Monthly Recurring Revenue (USD) */
  mrr: number;
  /** Annual Recurring Revenue = MRR * 12 */
  arr: number;
  /** Average Revenue Per User (USD) */
  arpu: number;
  /** Total active paying customers */
  activeCustomers: number;
  /** Total revenue collected this period */
  totalRevenue: number;
  /** Tier breakdown */
  tierDistribution: {
    free: number;
    starter: number;
    pro: number;
    enterprise: number;
  };
  computedAt: Timestamp;
}

/** Growth metrics */
export interface GrowthIndicator {
  period: AnalyticsPeriod;
  /** Month-over-month MRR growth percent */
  momGrowthPercent: number;
  /** Week-over-week growth percent */
  wowGrowthPercent: number;
  /** Monthly churn rate (0-1) */
  churnRate: number;
  /** Expansion revenue this period (upsells/upgrades) */
  expansionRevenue: number;
  /** Net Revenue Retention percent (NRR) */
  nrrPercent: number;
  /** New customers acquired */
  newCustomers: number;
  /** Churned customers */
  churnedCustomers: number;
  computedAt: Timestamp;
}

/** Full analytics bundle */
export interface AnalyticsBundle {
  roi: ROIMetrics;
  agents: AgentPerformance[];
  revenue: RevenueReport;
  growth: GrowthIndicator;
}
