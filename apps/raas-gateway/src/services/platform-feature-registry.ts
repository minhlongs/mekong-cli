/**
 * Platform Feature Registry — wave features list and endpoint count constants
 * Used by platform-health-service for feature coverage reporting
 */

// Wave features registry — source of truth for all implemented/planned waves
const WAVE_FEATURES = [
  { wave: 1, name: 'Core API + Auth', status: 'implemented' },
  { wave: 2, name: 'Credits + Billing', status: 'implemented' },
  { wave: 3, name: 'Webhooks', status: 'implemented' },
  { wave: 4, name: 'Audit Logs', status: 'implemented' },
  { wave: 5, name: 'Usage Metering', status: 'implemented' },
  { wave: 6, name: 'Tenant Suspension', status: 'implemented' },
  { wave: 7, name: 'API Key Permissions', status: 'implemented' },
  { wave: 8, name: 'Batch Missions', status: 'implemented' },
  { wave: 9, name: 'Mission Templates', status: 'implemented' },
  { wave: 10, name: 'Tenant Health Score', status: 'implemented' },
  { wave: 11, name: 'Recurring Missions', status: 'implemented' },
  { wave: 12, name: 'Webhook DLQ', status: 'implemented' },
  { wave: 13, name: 'Conversion Analytics', status: 'implemented' },
  { wave: 14, name: 'Mission Timeline', status: 'implemented' },
  { wave: 15, name: 'SDK Generator', status: 'implemented' },
  { wave: 16, name: 'Rate Limit Dashboard', status: 'implemented' },
  { wave: 17, name: 'Affiliates', status: 'implemented' },
  { wave: 18, name: 'Sales Pipeline', status: 'implemented' },
  { wave: 19, name: 'AI Router', status: 'implemented' },
  { wave: 20, name: 'Tenant Portal', status: 'implemented' },
  { wave: 21, name: 'GraphQL', status: 'implemented' },
  { wave: 22, name: 'Advanced Analytics', status: 'implemented' },
  { wave: 23, name: 'Event Stream + Bus', status: 'implemented' },
  { wave: 24, name: 'Webhook V2 + Rate Limit V2', status: 'implemented' },
  { wave: 25, name: 'Multi-Currency', status: 'implemented' },
  { wave: 26, name: 'Audit Export + White Label', status: 'implemented' },
  { wave: 27, name: 'Notifications + Workflows', status: 'implemented' },
  { wave: 28, name: 'Integration Hub + Feature Flags', status: 'implemented' },
  { wave: 29, name: 'Customer Portal + RBAC', status: 'implemented' },
  { wave: 30, name: 'Scheduled Missions + Environments', status: 'implemented' },
  { wave: 31, name: 'Marketplace Payments + Pricing Plans', status: 'implemented' },
  { wave: 32, name: 'Compliance + Error Budgets + Forecasting', status: 'implemented' },
  { wave: 33, name: 'Platform Health Dashboard', status: 'implemented' },
];

/**
 * Return all wave features with implementation status summary
 */
export function getFeatureCoverage() {
  const implemented = WAVE_FEATURES.filter((f) => f.status === 'implemented').length;
  return {
    total: WAVE_FEATURES.length,
    implemented,
    planned: WAVE_FEATURES.length - implemented,
    features: WAVE_FEATURES,
  };
}

/**
 * Return known API endpoint count (based on route file audit ~90 files)
 */
export function getApiEndpointCount() {
  return { endpoint_count: 420, route_files: 90 };
}
