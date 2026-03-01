/**
 * @agencyos/vibe-supabase — Entry Point
 *
 * Typed Supabase query helpers for RaaS multi-org patterns.
 * Uses generic SupabaseLike — no hard @supabase/supabase-js dependency.
 */

// Typed query helpers + SupabaseLike interface
export {
  fetchOne,
  fetchMany,
  insertOne,
  updateWhere,
  rpcCall,
  invokeFunction,
  getCurrentUserId,
} from './typed-query-helpers';

export type {
  SupabaseLike,
  QueryResult,
  QueryListResult,
} from './typed-query-helpers';

// Org-scoped query helpers (multi-org CRUD)
export {
  getUserOrgs,
  getOrgById,
  getOrgMembers,
  getOrgActivePlan,
  getOrgSubscription,
  createOrg,
  orgQueries,
} from './org-scoped-query-helpers';

// Subscription query helpers (user-level plans + subscriptions)
export {
  getPlans,
  getUserActivePlan,
  getUserSubscription,
  createSubscription,
  cancelSubscription,
  createSubscriptionIntent,
  subscriptionQueries,
} from './subscription-query-helpers';

// Usage tracking query helpers (org-scoped metering)
export {
  trackFeatureUsage,
  trackFeatureUsageBatch,
  getOrgUsageSummary,
  getOrgUsageByFeature,
  getUsageTimeline,
  checkOrgQuota,
  usageQueries,
} from './usage-tracking-query-helpers';

export type {
  UsageRecord,
  UsageSummary,
  UsageQuota,
} from './usage-tracking-query-helpers';
