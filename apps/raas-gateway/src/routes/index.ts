/**
 * Route registry — combines all route handlers
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { health } from './health';
import { api } from './api';
import { credits } from './credits';
import { billing } from './billing';
import { tenants } from './tenants';
import { onboarding } from './onboarding';
import { telegram } from './telegram';
import { alerts } from './alerts';
import { marketplace } from './marketplace';
import { stripe } from './stripe';
import { checkout } from './checkout';
import { admin } from './admin';
import { adminAnalytics } from './admin-analytics';
import { dunning } from './dunning';
import { licenses } from './licenses';
import { webhooks } from './webhooks';
import { status } from './status';
import { dashboard } from './dashboard';
import { playground } from './playground';
import { usageExport } from './usage-export';
import { referrals } from './referrals';
import { metrics } from './metrics';
import { apiDocs } from './api-docs';
import { projects } from './projects';
import { team } from './team';
import { webhookManagement } from './webhook-management';
import { audit } from './audit';
import { landing } from './landing';
import { usageMetering } from './usage-metering';
import { accountSuspension, adminSuspensions } from './suspension';
import { apiKeyManagement } from './api-key-management';
import { batchMissions } from './batch-missions';
import { marketplaceTemplates, missionTemplates } from './mission-templates';
import { tenantHealth } from './tenant-health';
import { recurringMissions } from './recurring-missions';
import { webhookDLQ } from './webhook-dlq';
import { conversionAnalytics } from './conversion-analytics';
import { missionTimeline } from './mission-timeline';
import { sdkGenerator } from './sdk-generator';
import { rateLimitDashboard } from './rate-limit-dashboard';
import { developerPortal } from './developer-portal';
import { changelog } from './changelog';
import { tenantImpersonation } from './tenant-impersonation';
import { tenantExport } from './tenant-export';
import { sso } from './sso';
import { statusBadge } from './status-badge';
import { notificationPreferences } from './notification-preferences';
import { models } from './models';
import { affiliates } from './affiliates';
import { salesPipeline } from './sales-pipeline';
import { salesTools } from './sales-tools';
import { aiRouter } from './ai-router';
import { affiliateHooks } from './affiliate-hooks';
import { tenantPortal } from './tenant-portal';
import { graphql } from './graphql';
import { advancedAnalytics } from './advanced-analytics';
import { eventStream } from './event-stream';
import { eventBus } from './event-bus';
import { webhookV2 } from './webhook-v2';
import { rateLimitV2 } from './rate-limit-v2';
import { tenantIsolationV2 } from './tenant-isolation';
import { deepHealth } from './deep-health';
import { slaMonitoring } from './sla-monitoring';
import { bulkOperations } from './bulk-operations';
import { multiCurrency } from './multi-currency';
import { auditExport } from './audit-export';
import { whiteLabel } from './white-label';
import { apiVersioning } from './api-versioning';
import { notifications } from './notifications';
import { workflows } from './workflows';
import { integrationHub } from './integration-hub';
import { featureFlags } from './feature-flags';
import { customerPortal } from './customer-portal';
import { environments } from './environments';
import { platformKpis } from './platform-kpis';
import { marketplacePayments } from './marketplace-payments';
import { scheduledMissions } from './scheduled-missions';
import { pricingPlans } from './pricing-plans';
import { rbac } from './rbac';
import { auditStreaming } from './audit-streaming';
import { ipAllowlist } from './ip-allowlist';
import { dataRetention } from './data-retention';
import { errorBudgets } from './error-budgets';
import { usageForecasting } from './usage-forecasting';
import { complianceReports } from './compliance-reports';
import { cronOrchestrator } from './cron-orchestrator';
import { platformHealth } from './platform-health';
import { revenueAnalyticsV2 } from './revenue-analytics-v2';
import { tenantLifecycle } from './tenant-lifecycle';
import { onboardingV2 } from './onboarding-v2';
import { adaptiveRateLimit } from './adaptive-rate-limit';
import { apiSandbox } from './api-sandbox';
import { tenantBackup } from './tenant-backup';
import { apiUsageAnalytics } from './api-usage-analytics';
import { webhookSimulator } from './webhook-simulator';
import { platformAuditTrail } from './platform-audit-trail';
import { multiRegionConfig } from './multi-region-config';
import { customDomains } from './custom-domains';
import { tenantCollaboration } from './tenant-collaboration';
import { agentMarketplace } from './agent-marketplace';
import { usageAlerts } from './usage-alerts';
import { migrationTools } from './migration-tools';
import { notificationsHub } from './notifications-hub';
import { tenantApiTokens } from './tenant-api-tokens';
import { missionWebhooksV3 } from './mission-webhooks-v3';
import { platformAnnouncements } from './platform-announcements';
import { tenantQuotas } from './tenant-quotas';
import { aiModelRegistry } from './ai-model-registry';
import { platformMetricsDashboard } from './platform-metrics-dashboard';
import { tenantSsoV2 } from './tenant-sso-v2';
import { apiGatewayCaching } from './api-gateway-caching';
import { missionDependencies } from './mission-dependencies';
import { tenantInvoicing } from './tenant-invoicing';
import { platformChangelogV2 } from './platform-changelog-v2';
import { adminCommandCenter } from './admin-command-center';
import { webhookAnalytics } from './webhook-analytics';
import { ratePlanManagement } from './rate-plan-management';
import { tenantAuditPolicies } from './tenant-audit-policies';
import { platformFeatureRequests } from './platform-feature-requests';
import { adminTenantManagement } from './admin-tenant-management';
import { tenantDataEncryption } from './tenant-data-encryption';
import { missionReplayDebug } from './mission-replay-debug';
import { apiRateLimitPolicies } from './api-rate-limit-policies';
import { tenantOnboardingChecklist } from './tenant-onboarding-checklist';
import { platformLocalization } from './platform-localization';
import { missionApprovalWorkflow } from './mission-approval-workflow';
import { platformSecurityPolicies } from './platform-security-policies';
import { adminUserManagement } from './admin-user-management';
import { tenantBillingHistory } from './tenant-billing-history';
import { apiGatewayMiddleware } from './api-gateway-middleware';
import { platformCapacityPlanning } from './platform-capacity-planning';
import { platformNotificationCenter } from './platform-notification-center';
import { missionTemplateLibrary } from './mission-template-library';
import { tenantApiKeyManagement as tenantApiKeyMgmt } from './tenant-api-key-management';
import { adminFeatureFlags } from './admin-feature-flags';
import { tenantResourceQuotas } from './tenant-resource-quotas';
import { tenantWebhooksV3 } from './tenant-webhooks-v3';
import { platformServiceMesh } from './platform-service-mesh';
import { missionSchedulingEngine } from './mission-scheduling-engine';
import { adminPlatformConfig } from './admin-platform-config';
import { apiContractTesting } from './api-contract-testing';
import { tenantSsoProviders } from './tenant-sso-providers';
import { missionPriorityQueue } from './mission-priority-queue';
import { platformAnalyticsDashboard } from './platform-analytics-dashboard';
import { tenantCustomFields } from './tenant-custom-fields';
import { adminDeploymentManager } from './admin-deployment-manager';
import { apiDocGenerator } from './api-documentation-generator';
import { platformRateLimitAnalytics } from './platform-rate-limit-analytics';
import { tenantIpGeolocation } from './tenant-ip-geolocation';
import { tenantTagSystem } from './tenant-tag-system';
import { adminSystemHealth } from './admin-system-health';
import { apiResponseCaching } from './api-response-caching';
import { tenantWorkspaceSettings } from './tenant-workspace-settings';
import { missionResultStorage } from './mission-result-storage';
import { platformEventLog } from './platform-event-log';
import { tenantAccessTokens } from './tenant-access-tokens';
import { adminTenantAnalytics } from './admin-tenant-analytics';
import { apiEndpointMonitoring } from './api-endpoint-monitoring';
import { dataRetentionPolicies } from './tenant-data-retention-policies';
import { missionExecutionHistory } from './mission-execution-history';
import { platformErrorBudget } from './platform-error-budget';
import { tenantApiVersioning } from './tenant-api-versioning';
import { tenantComplianceReporting } from './tenant-compliance-reporting';
import { tenantNotificationChannels } from './tenant-notification-channels';
import { platformAuditPolicies } from './platform-audit-policies';
import { tenantDataEncryptionKeys } from './tenant-data-encryption-keys';
import { adminTrafficShaping } from './admin-traffic-shaping';
import { tenantIntegrationMarketplace } from './tenant-integration-marketplace';
import { missionRetryPolicies } from './mission-retry-policies';
import { platformFeatureUsage } from './platform-feature-usage';
import { adminIncidentResponse } from './admin-incident-response';
import { tenantExportSchedules } from './tenant-export-schedules';
import { tenantSessionManagement } from './tenant-session-management';
import { missionQualityGates } from './mission-quality-gates';
import { platformResourcePools } from './platform-resource-pools';
import { tenantApiDocumentation } from './tenant-api-documentation';
import { adminChangeManagement } from './admin-change-management';
import { tenantUsageAlerts } from './tenant-usage-alerts';
import { tenantApiRateQuotas } from './tenant-api-rate-quotas';
import { missionExecutionMetrics } from './mission-execution-metrics';
import { platformServiceRegistry } from './platform-service-registry';
import { tenantDataMasking } from './tenant-data-masking';
import { adminDeploymentTracking } from './admin-deployment-tracking';
import { tenantApiResponseTransform } from './tenant-api-response-transform';
import { missionSlaCompliance } from './mission-sla-compliance';
import { platformLicenseManagement } from './platform-license-management';
import { tenantDataPipeline } from './tenant-data-pipeline';
import { adminPlatformBackup } from './admin-platform-backup';
import { tenantApiMockServer } from './tenant-api-mock-server';
import { tenantWebhookTemplates } from './tenant-webhook-templates';
import { missionCostOptimization } from './mission-cost-optimization';
import { platformTenantGrouping } from './platform-tenant-grouping';
import { adminPlatformAlerts } from './admin-platform-alerts';
import { tenantWorkflowAutomation } from './tenant-workflow-automation';
import { tenantApiChangelog } from './tenant-api-changelog';
import { missionQueuePriority } from './mission-queue-priority';
import { platformComplianceAudit } from './platform-compliance-audit';
import { tenantSecretVault } from './tenant-secret-vault';
import { adminPlatformMigration } from './admin-platform-migration';
import { tenantEventReplay } from './tenant-event-replay';
import { tenantApiDeprecation } from './tenant-api-deprecation';
import { missionArtifactStorage } from './mission-artifact-storage';
import { platformTenantScoring } from './platform-tenant-scoring';
import { tenantCustomMetrics } from './tenant-custom-metrics';
import { adminPlatformScaling } from './admin-platform-scaling';
import { tenantNotificationDigest } from './tenant-notification-digest';
import { tenantApiAccessControl } from './tenant-api-access-control';
import { missionFeedbackLoop } from './mission-feedback-loop';
import { platformCostDashboard } from './platform-cost-dashboard';
import { tenantDataClassification } from './tenant-data-classification';
import { adminTenantCommunication } from './admin-tenant-communication';
import { tenantIntegrationTesting } from './tenant-integration-testing';
import { tenantApiPlaygroundConfigs } from './tenant-api-playground-configs';
import { missionChainOrchestration } from './mission-chain-orchestration';
import { platformFeatureGating } from './platform-feature-gating';
import { tenantConsentManagement } from './tenant-consent-management';
import { adminPlatformDiagnostics } from './admin-platform-diagnostics';
import { tenantApiRateBurst } from './tenant-api-rate-burst';
import { tenantApiKeyRotation } from './tenant-api-key-rotation';
import { missionDependencyGraph } from './mission-dependency-graph';
import { adminPlatformChangelog } from './admin-platform-changelog';
import { tenantDataExport } from './tenant-data-export';
import { adminIncidentManagement } from './admin-incident-management';
import { tenantApiSandbox } from './tenant-api-sandbox';
import { tenantWebhookSignatures } from './tenant-webhook-signatures';
import { missionCostTracking } from './mission-cost-tracking';
import { adminPlatformMaintenance } from './admin-platform-maintenance';
import { tenantUsageAnalytics } from './tenant-usage-analytics';
import { adminTenantMigration } from './admin-tenant-migration';
import { tenantNotificationPreferences } from './tenant-notification-preferences';
import { tenantApiVersioningConfig } from './tenant-api-versioning-config';
import { missionQualityScoring } from './mission-quality-scoring';
import { adminPlatformCompliance } from './admin-platform-compliance';
import { tenantDataRetention } from './tenant-data-retention';
import { adminServiceRegistry } from './admin-service-registry';
import { tenantApiRatePolicies } from './tenant-api-rate-policies';
import { tenantApiGatewayLogs } from './tenant-api-gateway-logs';
import { missionBatchProcessing } from './mission-batch-processing';
import { adminPlatformMetrics } from './admin-platform-metrics';
import { tenantCustomDomains } from './tenant-custom-domains';
import { adminCapacityPlanning } from './admin-capacity-planning';
import { tenantApiThrottling } from './tenant-api-throttling';
import { tenantApiCircuitBreaker } from './tenant-api-circuit-breaker';
import { missionResourceAllocation } from './mission-resource-allocation';
import { adminPlatformAuditTrail } from './admin-platform-audit-trail';
import { tenantApiCachingConfig } from './tenant-api-caching-config';
import { adminReleaseManagement } from './admin-release-management';
import { tenantErrorTracking } from './tenant-error-tracking';
import { tenantApiLoadBalancing } from './tenant-api-load-balancing';
import { missionWorkflowEngine } from './mission-workflow-engine';
import { adminPlatformSecurityScan } from './admin-platform-security-scan';
import { tenantApiSchemaValidation } from './tenant-api-schema-validation';
import { adminDeploymentPipeline } from './admin-deployment-pipeline';
import { tenantPerformanceProfiling } from './tenant-performance-profiling';
import { notFound } from '../utils/response';

export function createRoutes() {
  const routes = new Hono<{ Bindings: Env }>();

  // Mount routes — public routes BEFORE /v1 api (which has auth middleware)
  routes.route('/admin', admin);
  routes.route('/admin/analytics', adminAnalytics);
  routes.route('/admin/kpis', platformKpis);
  routes.route('/admin/dunning', dunning);
  routes.route('/admin/webhooks', webhooks);
  routes.route('/health', health);
  routes.route('/status', status);
  routes.route('/marketplace', marketplace);
  routes.route('/v1/tenants', tenants);
  routes.route('/v1/onboarding', onboarding);
  // Licenses: verify + activate are PUBLIC; create + list require auth (per-route)
  routes.route('/v1/licenses', licenses);

  // Wave 13-14 routes BEFORE /v1 api to avoid shadowing
  routes.route('/v1/usage', usageMetering);
  routes.route('/v1/missions', batchMissions);
  routes.route('/v1/account', accountSuspension);
  routes.route('/v1/api-keys', apiKeyManagement);
  routes.route('/v1/templates', missionTemplates);
  routes.route('/marketplace/templates', marketplaceTemplates);
  routes.route('/admin/suspensions', adminSuspensions);

  // Wave 15-16 routes BEFORE /v1 api to avoid shadowing
  routes.route('/v1/health-score', tenantHealth);
  routes.route('/v1/recurring', recurringMissions);
  routes.route('/', webhookDLQ);
  routes.route('/conversion', conversionAnalytics);
  routes.route('/v1/timeline', missionTimeline);
  routes.route('/sdk', sdkGenerator);
  routes.route('/', rateLimitDashboard);
  routes.route('/', developerPortal);
  routes.route('/', changelog);
  routes.route('/', tenantImpersonation);
  routes.route('/', tenantExport);
  routes.route('/', sso);
  routes.route('/', statusBadge);
  routes.route('/', notificationPreferences);

  // Wave 19-20 routes
  routes.route('/v1/models', models);
  routes.route('/v1/affiliates', affiliates);
  routes.route('/admin/sales', salesPipeline);
  routes.route('/', salesTools);

  // Wave 21-22 routes
  routes.route('/v1/ai-router', aiRouter);
  routes.route('/v1/affiliate-hooks', affiliateHooks);
  routes.route('/v1/portal', tenantPortal);
  routes.route('/graphql', graphql);
  routes.route('/admin/advanced-analytics', advancedAnalytics);

  // Wave 27-28 routes
  routes.route('/v1/notifications', notifications);
  routes.route('/v1/workflows', workflows);
  routes.route('/v1/integrations', integrationHub);
  routes.route('/v1/feature-flags', featureFlags);
  routes.route('/v1/customer-portal', customerPortal);

  // Wave 29-30 routes
  routes.route('/v1/rbac', rbac);
  routes.route('/v1/scheduled-missions', scheduledMissions);
  routes.route('/v1/environments', environments);
  routes.route('/v1/marketplace-payments', marketplacePayments);
  routes.route('/v1/pricing', pricingPlans);

  // Wave 31-32 routes
  routes.route('/v1/audit-streaming', auditStreaming);
  routes.route('/v1/ip-allowlist', ipAllowlist);
  routes.route('/v1/data-retention', dataRetention);
  routes.route('/v1/error-budgets', errorBudgets);
  routes.route('/v1/usage-forecast', usageForecasting);
  routes.route('/v1/compliance', complianceReports);

  // Wave 33-34 routes
  routes.route('/v1/cron', cronOrchestrator);
  routes.route('/platform-health', platformHealth);
  routes.route('/v1/onboarding-v2', onboardingV2);
  routes.route('/admin/revenue-v2', revenueAnalyticsV2);
  routes.route('/v1/lifecycle', tenantLifecycle);
  routes.route('/v1/adaptive-rate-limit', adaptiveRateLimit);

  // Wave 35 routes
  routes.route('/v1/sandbox', apiSandbox);
  routes.route('/v1/backup', tenantBackup);
  routes.route('/v1/webhook-simulator', webhookSimulator);
  routes.route('/v1/api-analytics', apiUsageAnalytics);

  // Wave 36 routes
  routes.route('/admin/audit-trail', platformAuditTrail);
  routes.route('/v1/region', multiRegionConfig);

  // Wave 37 routes
  routes.route('/v1/custom-domains', customDomains);
  routes.route('/v1/collaboration', tenantCollaboration);
  routes.route('/v1/agent-marketplace', agentMarketplace);

  // Wave 38 routes
  routes.route('/v1/usage-alerts', usageAlerts);
  routes.route('/v1/migration', migrationTools);
  routes.route('/v1/notifications-hub', notificationsHub);

  // Wave 39 routes
  routes.route('/v1/api-tokens', tenantApiTokens);
  routes.route('/v1/mission-webhooks-v3', missionWebhooksV3);
  routes.route('/v1/announcements', platformAnnouncements);

  // Wave 40 routes
  routes.route('/v1/quotas', tenantQuotas);
  routes.route('/v1/ai-models', aiModelRegistry);
  routes.route('/admin/platform-metrics', platformMetricsDashboard);

  // Wave 41 routes
  routes.route('/v1/sso', tenantSsoV2);
  routes.route('/v1/cache', apiGatewayCaching);
  routes.route('/v1/mission-chains', missionDependencies);

  // Wave 42 routes
  routes.route('/v1/invoicing', tenantInvoicing);
  routes.route('/v1/changelog-v2', platformChangelogV2);
  routes.route('/admin/commands', adminCommandCenter);

  // Wave 43 routes
  routes.route('/v1/webhook-analytics', webhookAnalytics);
  routes.route('/v1/rate-plans', ratePlanManagement);
  routes.route('/v1/mission-costs', missionCostTracking);

  // Wave 44 routes
  routes.route('/v1/audit-policies', tenantAuditPolicies);
  routes.route('/v1/feature-requests', platformFeatureRequests);
  routes.route('/admin/tenant-mgmt', adminTenantManagement);

  // Wave 45 routes
  routes.route('/v1/encryption', tenantDataEncryption);
  routes.route('/v1/mission-debug', missionReplayDebug);
  routes.route('/v1/rate-policies', apiRateLimitPolicies);

  // Wave 46 routes
  routes.route('/v1/onboarding-checklist', tenantOnboardingChecklist);
  routes.route('/v1/i18n', platformLocalization);

  // Wave 47 routes
  routes.route('/v1/mission-approvals', missionApprovalWorkflow);
  routes.route('/v1/security-policies', platformSecurityPolicies);
  routes.route('/admin/user-mgmt', adminUserManagement);

  // Wave 48 routes
  routes.route('/v1/billing-history', tenantBillingHistory);
  routes.route('/v1/gateway-middleware', apiGatewayMiddleware);
  routes.route('/admin/capacity', platformCapacityPlanning);

  // Wave 49 routes
  routes.route('/v1/notification-center', platformNotificationCenter);
  routes.route('/v1/mission-templates', missionTemplateLibrary);
  routes.route('/v1/api-key-mgmt', tenantApiKeyMgmt);

  // Wave 50 routes
  routes.route('/v1/audit-trail', platformAuditTrail);
  routes.route('/admin/feature-flags', adminFeatureFlags);
  routes.route('/v1/resource-quotas', tenantResourceQuotas);

  // Wave 51 routes
  routes.route('/v1/webhooks-v3', tenantWebhooksV3);
  routes.route('/admin/service-mesh', platformServiceMesh);
  routes.route('/v1/scheduling', missionSchedulingEngine);

  // Wave 52 routes
  routes.route('/admin/platform-config', adminPlatformConfig);
  routes.route('/admin/contract-testing', apiContractTesting);

  // Wave 53 routes
  routes.route('/v1/sso-providers', tenantSsoProviders);
  routes.route('/v1/priority-queue', missionPriorityQueue);
  routes.route('/v1/analytics-dashboard', platformAnalyticsDashboard);

  // Wave 54 routes
  routes.route('/v1/custom-fields', tenantCustomFields);
  routes.route('/admin/deployments', adminDeploymentManager);
  routes.route('/admin/api-docs', apiDocGenerator);

  // Wave 55 routes
  routes.route('/v1/ip-geo', tenantIpGeolocation);
  routes.route('/v1/dep-graph', missionDependencyGraph);
  routes.route('/v1/rate-analytics', platformRateLimitAnalytics);

  // Wave 56 routes
  routes.route('/v1/tags', tenantTagSystem);
  routes.route('/admin/system-health', adminSystemHealth);
  routes.route('/admin/response-cache', apiResponseCaching);

  // Wave 57 routes
  routes.route('/v1/workspace', tenantWorkspaceSettings);
  routes.route('/v1/results', missionResultStorage);
  routes.route('/admin/event-log', platformEventLog);

  // Wave 58 routes
  routes.route('/v1/access-tokens', tenantAccessTokens);
  routes.route('/admin/tenant-analytics', adminTenantAnalytics);
  routes.route('/admin/endpoint-monitoring', apiEndpointMonitoring);

  // Wave 59 routes
  routes.route('/v1/data-retention', dataRetentionPolicies);
  routes.route('/v1/execution-history', missionExecutionHistory);
  routes.route('/admin/error-budget', platformErrorBudget);

  // Wave 60 routes
  routes.route('/v1/api-versioning', tenantApiVersioning);
  routes.route('/v1/compliance-reports', tenantComplianceReporting);

  // Wave 61 routes
  routes.route('/v1/notification-channels', tenantNotificationChannels);
  routes.route('/admin/audit-policies', platformAuditPolicies);

  // Wave 62 routes
  routes.route('/v1/encryption-keys', tenantDataEncryptionKeys);
  routes.route('/admin/traffic-shaping', adminTrafficShaping);
  routes.route('/v1/integrations', tenantIntegrationMarketplace);

  // Wave 63 routes
  routes.route('/v1/retry-policies', missionRetryPolicies);
  routes.route('/admin/feature-usage', platformFeatureUsage);

  // Wave 64 routes
  routes.route('/admin/incident-response', adminIncidentResponse);
  routes.route('/v1/export-schedules', tenantExportSchedules);

  // Wave 65 routes
  routes.route('/v1/sessions', tenantSessionManagement);
  routes.route('/v1/quality-gates', missionQualityGates);
  routes.route('/admin/resource-pools', platformResourcePools);

  // Wave 66 routes
  routes.route('/v1/api-docs-tenant', tenantApiDocumentation);
  routes.route('/admin/change-management', adminChangeManagement);
  routes.route('/v1/usage-alerts', tenantUsageAlerts);

  // Wave 67 routes
  routes.route('/v1/api-rate-quotas', tenantApiRateQuotas);
  routes.route('/v1/execution-metrics', missionExecutionMetrics);
  routes.route('/admin/service-registry', platformServiceRegistry);

  // Wave 68 routes
  routes.route('/v1/data-masking', tenantDataMasking);
  routes.route('/admin/deployment-tracking', adminDeploymentTracking);

  // Wave 69 routes
  routes.route('/v1/response-transform', tenantApiResponseTransform);
  routes.route('/v1/sla-compliance', missionSlaCompliance);
  routes.route('/admin/license-management', platformLicenseManagement);

  // Wave 70 routes
  routes.route('/v1/data-pipeline', tenantDataPipeline);
  routes.route('/admin/platform-backup', adminPlatformBackup);
  routes.route('/v1/api-mocks', tenantApiMockServer);

  // Wave 71 routes
  routes.route('/v1/webhook-templates', tenantWebhookTemplates);
  routes.route('/v1/cost-optimization', missionCostOptimization);
  routes.route('/admin/tenant-grouping', platformTenantGrouping);

  // Wave 72 routes
  routes.route('/admin/platform-alerts', adminPlatformAlerts);
  routes.route('/v1/workflow-automation', tenantWorkflowAutomation);

  // Wave 73 routes
  routes.route('/v1/api-changelog', tenantApiChangelog);
  routes.route('/v1/queue-priority', missionQueuePriority);
  routes.route('/admin/compliance-audit', platformComplianceAudit);

  // Wave 74 routes
  routes.route('/v1/secret-vault', tenantSecretVault);
  routes.route('/admin/platform-migration', adminPlatformMigration);
  routes.route('/v1/event-replay', tenantEventReplay);

  // Wave 75 routes
  routes.route('/v1/api-deprecation', tenantApiDeprecation);
  routes.route('/v1/artifact-storage', missionArtifactStorage);
  routes.route('/admin/tenant-scoring', platformTenantScoring);

  // Wave 76 routes
  routes.route('/v1/custom-metrics', tenantCustomMetrics);
  routes.route('/admin/platform-scaling', adminPlatformScaling);
  routes.route('/v1/notification-digest', tenantNotificationDigest);

  // Wave 77 routes
  routes.route('/v1/access-control', tenantApiAccessControl);
  routes.route('/v1/feedback-loop', missionFeedbackLoop);
  routes.route('/admin/cost-dashboard', platformCostDashboard);

  // Wave 78 routes
  routes.route('/v1/data-classification', tenantDataClassification);
  routes.route('/admin/tenant-communication', adminTenantCommunication);
  routes.route('/v1/integration-testing', tenantIntegrationTesting);

  // Wave 79 routes
  routes.route('/v1/playground-configs', tenantApiPlaygroundConfigs);
  routes.route('/v1/chain-orchestration', missionChainOrchestration);
  routes.route('/admin/feature-gating', platformFeatureGating);

  // Wave 80 routes
  routes.route('/v1/consent-management', tenantConsentManagement);
  routes.route('/admin/platform-diagnostics', adminPlatformDiagnostics);
  routes.route('/v1/rate-burst', tenantApiRateBurst);

  // Wave 81 routes
  routes.route('/v1/key-rotation', tenantApiKeyRotation);
  routes.route('/v1/dependency-graph', missionDependencyGraph);
  routes.route('/admin/platform-changelog', adminPlatformChangelog);

  // Wave 82 routes
  routes.route('/v1/data-export', tenantDataExport);
  routes.route('/admin/incident-management', adminIncidentManagement);
  routes.route('/v1/api-sandbox', tenantApiSandbox);

  // Wave 83 routes
  routes.route('/v1/webhook-signatures', tenantWebhookSignatures);
  routes.route('/v1/cost-tracking', missionCostTracking);
  routes.route('/admin/platform-maintenance', adminPlatformMaintenance);

  // Wave 84 routes
  routes.route('/v1/usage-analytics', tenantUsageAnalytics);
  routes.route('/admin/tenant-migration', adminTenantMigration);
  routes.route('/v1/notification-preferences', tenantNotificationPreferences);

  // Wave 85 routes
  routes.route('/v1/versioning-config', tenantApiVersioningConfig);
  routes.route('/v1/quality-scoring', missionQualityScoring);
  routes.route('/admin/platform-compliance', adminPlatformCompliance);

  // Wave 86 routes
  routes.route('/v1/data-retention', tenantDataRetention);
  routes.route('/admin/service-registry', adminServiceRegistry);
  routes.route('/v1/rate-policies', tenantApiRatePolicies);

  // Wave 87 routes
  routes.route('/v1/gateway-logs', tenantApiGatewayLogs);
  routes.route('/v1/batch-processing', missionBatchProcessing);
  routes.route('/admin/platform-metrics', adminPlatformMetrics);

  // Wave 88 routes
  routes.route('/v1/custom-domains', tenantCustomDomains);
  routes.route('/admin/capacity-planning', adminCapacityPlanning);
  routes.route('/v1/api-throttling', tenantApiThrottling);

  // Wave 89 routes
  routes.route('/v1/circuit-breaker', tenantApiCircuitBreaker);
  routes.route('/v1/resource-allocation', missionResourceAllocation);
  routes.route('/admin/audit-trail', adminPlatformAuditTrail);

  // Wave 90 routes
  routes.route('/v1/caching-config', tenantApiCachingConfig);
  routes.route('/admin/release-management', adminReleaseManagement);
  routes.route('/v1/error-tracking', tenantErrorTracking);

  // Wave 91 routes
  routes.route('/v1/load-balancing', tenantApiLoadBalancing);
  routes.route('/v1/workflow-engine', missionWorkflowEngine);
  routes.route('/admin/security-scan', adminPlatformSecurityScan);

  // Wave 92 routes
  routes.route('/v1/schema-validation', tenantApiSchemaValidation);
  routes.route('/admin/deployment-pipeline', adminDeploymentPipeline);
  routes.route('/v1/performance-profiling', tenantPerformanceProfiling);

  // Wave 25-26 routes
  routes.route('/v1/currencies', multiCurrency);
  routes.route('/v1/audit', auditExport);
  routes.route('/v1/branding', whiteLabel);
  routes.route('/api/versions', apiVersioning);
  routes.route('/v1/bulk', bulkOperations);
  routes.route('/sla', slaMonitoring);

  // Wave 23-24 routes
  routes.route('/v1/events', eventStream);
  routes.route('/v1/event-bus', eventBus);
  routes.route('/v1/webhooks-v2', webhookV2);
  routes.route('/v1/rate-limits', rateLimitV2);
  routes.route('/v1/isolation', tenantIsolationV2);
  routes.route('/health/deep', deepHealth);

  routes.route('/v1', api);
  routes.route('/v1', dashboard);
  routes.route('/v1/usage', usageExport);
  routes.route('/v1/invoices', usageExport);
  routes.route('/', landing);
  routes.route('/', playground);
  routes.route('/v1/alerts', alerts);
  routes.route('/credits', credits);
  routes.route('/billing', billing);
  // Stripe: /billing/stripe/webhook is PUBLIC (no global auth), /billing/stripe/checkout has its own auth()
  routes.route('/billing/stripe', stripe);
  routes.route('/billing/checkout', checkout);
  routes.route('/webhook/telegram', telegram);
  routes.route('/metrics', metrics);
  routes.route('/docs', apiDocs);
  routes.route('/v1/referrals', referrals);
  routes.route('/v1/projects', projects);
  routes.route('/v1/team', team);
  routes.route('/v1/webhooks', webhookManagement);
  routes.route('/v1/audit', audit);

  // Waitlist email capture (public)
  routes.post('/waitlist', async (c) => {
    const body = await c.req.json().catch(() => ({}));
    const email = body.email?.trim()?.toLowerCase();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return c.json({ error: 'Valid email required' }, 400);
    }
    try {
      await c.env.DB.prepare(
        "INSERT OR IGNORE INTO waitlist (id, email, source, created_at) VALUES (?, ?, ?, datetime('now'))"
      ).bind(crypto.randomUUID(), email, body.source || 'landing').run();
      return c.json({ success: true, message: 'You\'re on the list!' });
    } catch {
      return c.json({ success: true, message: 'Already on the list!' });
    }
  });

  // Public mission sharing (no auth)
  routes.get('/share/:id', async (c) => {
    const missionId = c.req.param('id');
    const mission = await c.env.DB.prepare(
      `SELECT goal, complexity, status, result, credits_cost, created_at, completed_at
       FROM missions WHERE id = ? AND is_public = 1`
    ).bind(missionId).first<any>();

    if (!mission) {
      return c.json({ error: 'Mission not found or not public' }, 404);
    }

    // Return as HTML for social sharing
    const html = `<!DOCTYPE html><html><head>
      <title>Mekong Mission Result</title>
      <meta property="og:title" content="AI Mission: ${mission.goal.slice(0, 60)}">
      <meta property="og:description" content="${(mission.result || '').slice(0, 150)}">
      <style>body{font-family:system-ui;background:#0a0a0a;color:#e5e5e5;max-width:700px;margin:2rem auto;padding:1rem}
      h1{color:#22d3ee;font-size:1.2rem}pre{background:#111;padding:1rem;border-radius:8px;white-space:pre-wrap;font-size:0.9rem}
      .meta{color:#888;font-size:0.85rem}a{color:#22d3ee}</style></head><body>
      <h1>${mission.goal}</h1>
      <p class="meta">${mission.complexity} | ${mission.credits_cost} MCU | ${mission.status}</p>
      <pre>${mission.result || 'Processing...'}</pre>
      <p class="meta">Powered by <a href="https://mekong-raas.pages.dev">Mekong CLI</a></p>
      </body></html>`;
    return c.html(html);
  });

  // Public stats — cached in KV for 5 min
  routes.get('/stats', async (c) => {
    const cached = await c.env.RATE_LIMIT_KV.get('public:stats', 'json') as any;
    if (cached) return c.json(cached);

    const [tenants, missions, credits] = await Promise.all([
      c.env.DB.prepare('SELECT COUNT(*) as c FROM tenants WHERE active=1').first<{c:number}>(),
      c.env.DB.prepare("SELECT COUNT(*) as c FROM missions WHERE status='completed'").first<{c:number}>(),
      c.env.DB.prepare('SELECT COALESCE(SUM(total_spent),0) as c FROM tenants').first<{c:number}>(),
    ]);

    const stats = {
      tenants: tenants?.c ?? 0,
      missionsCompleted: missions?.c ?? 0,
      creditsProcessed: credits?.c ?? 0,
      updatedAt: new Date().toISOString(),
    };

    await c.env.RATE_LIMIT_KV.put('public:stats', JSON.stringify(stats), { expirationTtl: 300 });
    return c.json(stats);
  });

  // OpenAPI spec
  routes.get('/openapi.json', (c) => {
    return c.json({
      openapi: '3.0.3',
      info: { title: 'Mekong RaaS Gateway', version: '1.0.0', description: 'AI-Operated Business Platform API' },
      servers: [{ url: 'https://raas-gateway.agencyos-openclaw.workers.dev' }],
      paths: {
        '/v1/tenants/signup': { post: { summary: 'Create account', tags: ['Tenants'], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { name: { type: 'string' }, email: { type: 'string' } }, required: ['name','email'] } } } }, responses: { '201': { description: 'Account created with JWT + 10 credits' } } } },
        '/v1/tenants/profile': { get: { summary: 'Get profile', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/api-keys': { post: { summary: 'Generate API key', tags: ['Tenants'], security: [{ bearer: [] }] }, get: { summary: 'List API keys', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/api-keys/{id}': { delete: { summary: 'Revoke API key', tags: ['Tenants'], security: [{ bearer: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/missions': { post: { summary: 'Submit mission (1-5 MCU)', tags: ['Missions'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { goal: { type: 'string' }, complexity: { type: 'string', enum: ['simple','standard','complex'] }, project: { type: 'string' }, callback_url: { type: 'string' } }, required: ['goal'] } } } } }, get: { summary: 'List missions', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}': { get: { summary: 'Get mission + result', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}/cancel': { post: { summary: 'Cancel + refund', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/analytics': { get: { summary: 'Usage dashboard', tags: ['Analytics'], security: [{ bearer: [] }] } },
        '/credits': { get: { summary: 'Credit balance', tags: ['Credits'], security: [{ bearer: [] }] } },
        '/credits/check': { post: { summary: 'Pre-check cost', tags: ['Credits'], security: [{ bearer: [] }] } },
        '/billing/pricing': { get: { summary: 'Pricing tiers', tags: ['Billing'] } },
        '/billing/webhook': { post: { summary: 'Polar webhook', tags: ['Billing'] } },
        '/marketplace': { get: { summary: 'Browse public missions', tags: ['Marketplace'], parameters: [{ name: 'q', in: 'query', schema: { type: 'string' } }, { name: 'limit', in: 'query', schema: { type: 'integer' } }] } },
        '/marketplace/featured': { get: { summary: 'Featured missions', tags: ['Marketplace'] } },
        '/marketplace/stats': { get: { summary: 'Marketplace statistics', tags: ['Marketplace'] } },
        '/v1/alerts': { get: { summary: 'List unread alerts', tags: ['Alerts'], security: [{ bearer: [] }] } },
        '/v1/alerts/count': { get: { summary: 'Unread alert count', tags: ['Alerts'], security: [{ bearer: [] }] } },
        '/billing/stripe/packs': { get: { summary: 'List credit packs', tags: ['Billing'] } },
        '/billing/stripe/checkout': { post: { summary: 'Create Stripe checkout', tags: ['Billing'], security: [{ bearer: [] }] } },
        '/billing/stripe/webhook': { post: { summary: 'Stripe webhook', tags: ['Billing'] } },
        '/health': { get: { summary: 'Health check', tags: ['System'] } },
        '/stats': { get: { summary: 'Public stats', tags: ['System'] } },
        '/marketplace/leaderboard': { get: { summary: 'Referral leaderboard', tags: ['Marketplace'] } },
        '/marketplace/{id}/reviews': {
          get: { summary: 'Mission reviews', tags: ['Marketplace'], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }] },
          post: { summary: 'Submit review', tags: ['Marketplace'], security: [{ bearer: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { rating: { type: 'integer' }, comment: { type: 'string' } }, required: ['rating'] } } } } },
        },
        '/v1/missions/templates': { get: { summary: 'Mission templates (DB-backed)', tags: ['Missions'], parameters: [{ name: 'category', in: 'query', schema: { type: 'string' } }] } },
        '/v1/tenants/settings': { put: { summary: 'Update tenant settings', tags: ['Tenants'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { webhook_url: { type: 'string' }, notify_email: { type: 'boolean' }, notify_telegram: { type: 'boolean' } } } } } } } },
        '/v1/tenants/trial-extend': { post: { summary: 'Trial extension', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/usage': { get: { summary: 'Monthly usage', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/invoices': { get: { summary: 'Invoice history', tags: ['Tenants'], security: [{ bearer: [] }], parameters: [{ name: 'limit', in: 'query', schema: { type: 'integer' } }, { name: 'offset', in: 'query', schema: { type: 'integer' } }, { name: 'type', in: 'query', schema: { type: 'string' } }] } },
        '/v1/credits/redeem': { post: { summary: 'Redeem coupon', tags: ['Credits'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { code: { type: 'string' } }, required: ['code'] } } } } } },
        '/v1/credits/feedback': { post: { summary: 'Submit feedback', tags: ['Credits'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { type: { type: 'string' }, message: { type: 'string' } }, required: ['type', 'message'] } } } } } },
        '/admin/revenue/daily': { get: { summary: 'Daily revenue', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/mrr': { get: { summary: 'MRR calculation', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/churn': { get: { summary: 'Churn stats', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/ltv': { get: { summary: 'LTV analytics', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/forecast': { get: { summary: 'Revenue forecast', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/coupons': {
          get: { summary: 'List coupons', tags: ['Admin'], security: [{ bearer: [] }] },
          post: { summary: 'Create coupon', tags: ['Admin'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object' } } } } },
        },
        '/admin/rate-limits/{tenantId}': { get: { summary: 'Rate limit status', tags: ['Admin'], security: [{ bearer: [] }], parameters: [{ name: 'tenantId', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/admin/errors': { get: { summary: 'Error log', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/v1/onboarding/checklist': { get: { summary: 'Onboarding checklist', tags: ['Onboarding'], security: [{ bearer: [] }] } },
        '/v1/onboarding/complete': { post: { summary: 'Complete onboarding step', tags: ['Onboarding'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { step: { type: 'string' } }, required: ['step'] } } } } } },
        '/v1/onboarding/tips': { get: { summary: 'Quickstart tips (public)', tags: ['Onboarding'] } },
        '/admin/webhooks/logs': { get: { summary: 'Webhook delivery logs', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/webhooks/dead-letter': { get: { summary: 'Dead letter queue', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/webhooks/retry/{id}': { post: { summary: 'Retry webhook delivery', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/webhooks/stats': { get: { summary: 'Webhook delivery stats', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/status': { get: { summary: 'System status', tags: ['System'] } },
        '/status/incidents': { get: { summary: 'Recent incidents', tags: ['System'] } },
        '/status/history': { get: { summary: 'Uptime history', tags: ['System'] } },
        '/admin/dunning/active': { get: { summary: 'Active dunning cases', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/stats': { get: { summary: 'Dunning statistics', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/resolve/{id}': { post: { summary: 'Resolve dunning case', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/win-back': { get: { summary: 'Win-back campaign stats', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/win-back/{tenantId}': { post: { summary: 'Trigger win-back email', tags: ['Admin'], security: [{ bearer: [] }], parameters: [{ name: 'tenantId', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/licenses': { post: { summary: 'Generate license key', tags: ['Licenses'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { type: { type: 'string', enum: ['personal','team','enterprise','oem'] }, email: { type: 'string' }, name: { type: 'string' } }, required: ['type'] } } } } }, get: { summary: 'List licenses', tags: ['Licenses'], security: [{ bearer: [] }] } },
        '/v1/licenses/verify/{key}': { get: { summary: 'Verify license key (public)', tags: ['Licenses'], parameters: [{ name: 'key', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/licenses/activate/{key}': { post: { summary: 'Activate license (public)', tags: ['Licenses'], parameters: [{ name: 'key', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/missions/{id}/share': { post: { summary: 'Make mission public', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}/poll': { get: { summary: 'Lightweight status poll', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/dashboard': { get: { summary: 'Tenant aggregated stats', tags: ['Dashboard'], security: [{ bearer: [] }], responses: { '200': { description: 'Mission counts, credit summary, webhook success rate, recent missions' } } } },
        '/playground': { get: { summary: 'Interactive API explorer', tags: ['System'], responses: { '200': { description: 'HTML page with API playground UI' } } } },
        '/v1/usage/export': { get: { summary: 'Export credit transactions as CSV', tags: ['Usage'], security: [{ bearer: [] }], parameters: [{ name: 'format', in: 'query', schema: { type: 'string', enum: ['csv'] } }, { name: 'from', in: 'query', schema: { type: 'string', format: 'date' } }, { name: 'to', in: 'query', schema: { type: 'string', format: 'date' } }], responses: { '200': { description: 'CSV file download', content: { 'text/csv': { schema: { type: 'string' } } } } } } },
        '/v1/invoices': { get: { summary: 'List invoices (subscriptions + credit purchases)', tags: ['Billing'], security: [{ bearer: [] }], responses: { '200': { description: 'Invoice list with id, date, amount, currency, status, description, items' } } } },
        '/v1/invoices/{id}': { get: { summary: 'Get single invoice detail', tags: ['Billing'], security: [{ bearer: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Invoice detail' }, '404': { description: 'Invoice not found' } } } },
        '/billing/checkout': { post: { summary: 'Create Polar checkout session', tags: ['Billing'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { product_id: { type: 'string' }, success_url: { type: 'string' }, cancel_url: { type: 'string' } }, required: ['product_id'] } } } } } },
        '/billing/checkout/products': { get: { summary: 'List purchasable products', tags: ['Billing'] } },
        '/v1/tenants/limits': { get: { summary: 'Rate limits and usage quotas', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/metrics': { get: { summary: 'Request metrics (24h)', tags: ['System'] } },
        '/metrics/live': { get: { summary: 'Live metrics (current hour)', tags: ['System'] } },
        '/docs': { get: { summary: 'API reference docs', tags: ['System'] } },
        '/v1/referrals/generate': { post: { summary: 'Generate referral code', tags: ['Referrals'], security: [{ bearer: [] }] } },
        '/v1/referrals/stats': { get: { summary: 'Referral stats dashboard', tags: ['Referrals'], security: [{ bearer: [] }] } },
        '/v1/referrals/apply': { post: { summary: 'Apply referral code', tags: ['Referrals'], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { code: { type: 'string' }, email: { type: 'string' } }, required: ['code', 'email'] } } } } } },
        '/v1/projects': { post: { summary: 'Create project', tags: ['Projects'], security: [{ bearer: [] }] }, get: { summary: 'List projects', tags: ['Projects'], security: [{ bearer: [] }] } },
        '/v1/projects/{id}': { get: { summary: 'Get project', tags: ['Projects'], security: [{ bearer: [] }] }, delete: { summary: 'Archive project', tags: ['Projects'], security: [{ bearer: [] }] } },
        '/v1/projects/{id}/missions': { get: { summary: 'Project missions', tags: ['Projects'], security: [{ bearer: [] }] } },
        '/v1/team/invite': { post: { summary: 'Invite team member (pro+)', tags: ['Team'], security: [{ bearer: [] }] } },
        '/v1/team/members': { get: { summary: 'List team members', tags: ['Team'], security: [{ bearer: [] }] } },
        '/v1/team/members/{id}': { put: { summary: 'Update member role', tags: ['Team'], security: [{ bearer: [] }] }, delete: { summary: 'Remove member', tags: ['Team'], security: [{ bearer: [] }] } },
        '/v1/webhooks/events': { get: { summary: 'List webhook event types', tags: ['Webhooks'], security: [{ bearer: [] }] } },
        '/v1/webhooks/test': { post: { summary: 'Send test webhook', tags: ['Webhooks'], security: [{ bearer: [] }] } },
        '/v1/webhooks/config': { get: { summary: 'Webhook configuration', tags: ['Webhooks'], security: [{ bearer: [] }] } },
        '/v1/audit': { get: { summary: 'Tenant audit log', tags: ['Audit'], security: [{ bearer: [] }], parameters: [{ name: 'limit', in: 'query', schema: { type: 'integer' } }, { name: 'offset', in: 'query', schema: { type: 'integer' } }] } },
        '/v1/usage/current': { get: { summary: 'Current daily + monthly usage', tags: ['Usage'], security: [{ bearer: [] }] } },
        '/v1/usage/history': { get: { summary: 'Usage history', tags: ['Usage'], security: [{ bearer: [] }], parameters: [{ name: 'days', in: 'query', schema: { type: 'integer' } }] } },
        '/v1/usage/quotas': { post: { summary: 'Set usage quotas (admin)', tags: ['Usage'], security: [{ bearer: [] }] } },
        '/v1/usage/overage': { get: { summary: 'Overage charges', tags: ['Usage'], security: [{ bearer: [] }] } },
        '/v1/account/status': { get: { summary: 'Account suspension status', tags: ['Account'], security: [{ bearer: [] }] } },
        '/v1/account/reactivate': { post: { summary: 'Reactivate suspended account', tags: ['Account'], security: [{ bearer: [] }] } },
        '/admin/suspensions': { get: { summary: 'List suspended tenants', tags: ['Admin'] }, post: { summary: 'Suspend tenant', tags: ['Admin'] } },
        '/admin/suspensions/{tenantId}': { delete: { summary: 'Resume tenant', tags: ['Admin'] } },
        '/v1/api-keys': { post: { summary: 'Create API key with scope', tags: ['API Keys'], security: [{ bearer: [] }] }, get: { summary: 'List API keys', tags: ['API Keys'], security: [{ bearer: [] }] } },
        '/v1/api-keys/{id}': { get: { summary: 'Get API key detail', tags: ['API Keys'], security: [{ bearer: [] }] }, put: { summary: 'Update API key', tags: ['API Keys'], security: [{ bearer: [] }] }, delete: { summary: 'Revoke API key', tags: ['API Keys'], security: [{ bearer: [] }] } },
        '/v1/api-keys/{id}/rotate': { post: { summary: 'Rotate API key', tags: ['API Keys'], security: [{ bearer: [] }] } },
        '/v1/missions/batch': { post: { summary: 'Batch submit missions (max 50)', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/batch/{batchId}': { get: { summary: 'Get batch status', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/marketplace/templates': { get: { summary: 'Browse mission templates', tags: ['Marketplace'] } },
        '/marketplace/templates/{slug}': { get: { summary: 'Get template by slug', tags: ['Marketplace'] } },
        '/v1/templates': { post: { summary: 'Create custom template', tags: ['Templates'], security: [{ bearer: [] }] }, get: { summary: 'List templates', tags: ['Templates'], security: [{ bearer: [] }] } },
        '/v1/templates/{id}': { get: { summary: 'Get template', tags: ['Templates'], security: [{ bearer: [] }] }, put: { summary: 'Update template', tags: ['Templates'], security: [{ bearer: [] }] }, delete: { summary: 'Delete template', tags: ['Templates'], security: [{ bearer: [] }] } },
        '/v1/templates/{id}/use': { post: { summary: 'Create mission from template', tags: ['Templates'], security: [{ bearer: [] }] } },
        '/v1/templates/{id}/rate': { post: { summary: 'Rate template', tags: ['Templates'], security: [{ bearer: [] }] } },
        '/v1/health-score': { get: { summary: 'Current tenant health score', tags: ['Health Score'], security: [{ bearer: [] }] } },
        '/v1/health-score/history': { get: { summary: 'Health score history', tags: ['Health Score'], security: [{ bearer: [] }] } },
        '/v1/health-score/factors': { get: { summary: 'Health score factor breakdown', tags: ['Health Score'], security: [{ bearer: [] }] } },
        '/v1/recurring': { post: { summary: 'Create recurring mission', tags: ['Recurring Missions'], security: [{ bearer: [] }] }, get: { summary: 'List recurring missions', tags: ['Recurring Missions'], security: [{ bearer: [] }] } },
        '/v1/recurring/{id}': { get: { summary: 'Get recurring mission', tags: ['Recurring Missions'], security: [{ bearer: [] }] }, put: { summary: 'Update recurring mission', tags: ['Recurring Missions'], security: [{ bearer: [] }] }, delete: { summary: 'Deactivate recurring mission', tags: ['Recurring Missions'], security: [{ bearer: [] }] } },
        '/v1/recurring/{id}/trigger': { post: { summary: 'Manually trigger recurring mission', tags: ['Recurring Missions'], security: [{ bearer: [] }] } },
        '/v1/dlq': { get: { summary: 'Tenant DLQ entries', tags: ['Webhook DLQ'], security: [{ bearer: [] }] } },
        '/v1/dlq/stats': { get: { summary: 'Tenant DLQ stats', tags: ['Webhook DLQ'], security: [{ bearer: [] }] } },
        '/admin/dlq': { get: { summary: 'All DLQ entries (admin)', tags: ['Webhook DLQ'] } },
        '/admin/dlq/{id}/replay': { post: { summary: 'Replay DLQ entry', tags: ['Webhook DLQ'] } },
        '/admin/dlq/stats': { get: { summary: 'DLQ statistics', tags: ['Webhook DLQ'] } },
        '/conversion/track': { post: { summary: 'Track conversion event', tags: ['Conversion Analytics'] } },
        '/conversion/funnel': { get: { summary: 'Funnel visualization', tags: ['Conversion Analytics'] } },
        '/conversion/rates': { get: { summary: 'Conversion rates', tags: ['Conversion Analytics'] } },
        '/conversion/cohorts': { get: { summary: 'Cohort retention analysis', tags: ['Conversion Analytics'] } },
        '/conversion/sources': { get: { summary: 'Top acquisition sources', tags: ['Conversion Analytics'] } },
        '/v1/timeline/missions/{id}/timeline': { get: { summary: 'Mission timeline events', tags: ['Mission Timeline'], security: [{ bearer: [] }] } },
        '/v1/timeline/missions/{id}/trace': { get: { summary: 'Mission trace summary', tags: ['Mission Timeline'], security: [{ bearer: [] }] } },
        '/v1/timeline/traces': { get: { summary: 'List tenant traces', tags: ['Mission Timeline'], security: [{ bearer: [] }] } },
        '/v1/timeline/performance': { get: { summary: 'Performance stats', tags: ['Mission Timeline'], security: [{ bearer: [] }] } },
        '/sdk/endpoints': { get: { summary: 'List API endpoints for SDK', tags: ['SDK Generator'] } },
        '/sdk/snippet': { get: { summary: 'Generate code snippet', tags: ['SDK Generator'] } },
        '/sdk/{language}': { get: { summary: 'Generate full SDK client', tags: ['SDK Generator'] } },
        '/v1/rate-limits': { get: { summary: 'Tenant rate limit status', tags: ['Rate Limits'], security: [{ bearer: [] }] } },
        '/v1/rate-limits/history': { get: { summary: 'Rate limit hit history', tags: ['Rate Limits'], security: [{ bearer: [] }] } },
        '/admin/rate-limits/violations': { get: { summary: 'Rate limit violations', tags: ['Rate Limits'] } },
        '/developers': { get: { summary: 'Developer portal', tags: ['Portal'] } },
        '/changelog': { get: { summary: 'Changelog entries', tags: ['Portal'] } },
        '/changelog/latest': { get: { summary: 'Latest changelog', tags: ['Portal'] } },
        '/changelog/rss': { get: { summary: 'Changelog RSS feed', tags: ['Portal'] } },
        '/admin/impersonate': { post: { summary: 'Impersonate tenant', tags: ['Admin'] } },
        '/admin/impersonate/active': { get: { summary: 'Active impersonation sessions', tags: ['Admin'] } },
        '/admin/isolation/violations': { get: { summary: 'Isolation violations', tags: ['Admin'] } },
        '/v1/export': { get: { summary: 'Export tenant data (GDPR)', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/v1/data': { delete: { summary: 'GDPR delete request', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/admin/tenants/{id}/export': { get: { summary: 'Admin export tenant data', tags: ['Admin'] } },
        '/admin/tenants/{id}/data': { delete: { summary: 'Admin delete tenant data', tags: ['Admin'] } },
        '/v1/sso/config': { get: { summary: 'SSO config', tags: ['SSO'], security: [{ bearer: [] }] }, post: { summary: 'Update SSO config', tags: ['SSO'], security: [{ bearer: [] }] } },
        '/v1/sso/metadata': { get: { summary: 'SAML metadata', tags: ['SSO'] } },
        '/badge/status': { get: { summary: 'Status badge SVG', tags: ['Badges'] } },
        '/badge/version': { get: { summary: 'Version badge SVG', tags: ['Badges'] } },
        '/badge/missions': { get: { summary: 'Missions count badge', tags: ['Badges'] } },
        '/v1/notifications/preferences': { get: { summary: 'Notification preferences', tags: ['Notifications'], security: [{ bearer: [] }] }, put: { summary: 'Update notification preferences', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/channels': { get: { summary: 'Available channels', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/test': { post: { summary: 'Send test notification', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/models': { get: { summary: 'List AI models', tags: ['Models'], security: [{ bearer: [] }] } },
        '/v1/models/{id}': { get: { summary: 'Get model details', tags: ['Models'], security: [{ bearer: [] }] } },
        '/v1/models/select': { post: { summary: 'Auto-select optimal model', tags: ['Models'], security: [{ bearer: [] }] } },
        '/v1/affiliates/register': { post: { summary: 'Register as affiliate', tags: ['Affiliates'], security: [{ bearer: [] }] } },
        '/v1/affiliates/stats': { get: { summary: 'Affiliate stats', tags: ['Affiliates'], security: [{ bearer: [] }] } },
        '/v1/affiliates/commissions': { get: { summary: 'Affiliate commissions', tags: ['Affiliates'], security: [{ bearer: [] }] } },
        '/v1/affiliates/referrals': { get: { summary: 'Affiliate referrals', tags: ['Affiliates'], security: [{ bearer: [] }] } },
        '/v1/affiliates/admin': { get: { summary: 'List all partners', tags: ['Admin'] } },
        '/v1/affiliates/admin/leaderboard': { get: { summary: 'Affiliate leaderboard', tags: ['Admin'] } },
        '/admin/sales/leads': { post: { summary: 'Create sales lead', tags: ['Sales'] }, get: { summary: 'List leads', tags: ['Sales'] } },
        '/admin/sales/leads/{id}': { get: { summary: 'Lead details', tags: ['Sales'] }, put: { summary: 'Update lead', tags: ['Sales'] } },
        '/admin/sales/leads/{id}/stage': { put: { summary: 'Update lead stage', tags: ['Sales'] } },
        '/admin/sales/pipeline': { get: { summary: 'Pipeline view', tags: ['Sales'] } },
        '/admin/sales/forecast': { get: { summary: 'Revenue forecast', tags: ['Sales'] } },
        '/tools/roi-calculator': { post: { summary: 'Calculate ROI', tags: ['Sales Tools'] } },
        '/tools/demo/request': { post: { summary: 'Request demo sandbox', tags: ['Sales Tools'] } },
        '/tools/trial/signup': { post: { summary: 'Start free trial', tags: ['Sales Tools'] } },
        '/admin/sales/demos': { get: { summary: 'List demo sandboxes', tags: ['Admin'] } },
        '/admin/sales/trials': { get: { summary: 'List trial signups', tags: ['Admin'] } },
        '/admin/sales/trials/metrics': { get: { summary: 'Trial conversion metrics', tags: ['Admin'] } },
        // Wave 21: AI Router
        '/v1/ai-router': { get: { summary: 'Model recommendation for tenant', tags: ['AI Router'], security: [{ bearer: [] }] } },
        '/v1/ai-router/select': { post: { summary: 'Select model for mission', tags: ['AI Router'], security: [{ bearer: [] }] } },
        '/v1/ai-router/stats': { get: { summary: 'Model usage statistics', tags: ['AI Router'], security: [{ bearer: [] }] } },
        '/v1/ai-router/usage': { get: { summary: 'Tenant model usage history', tags: ['AI Router'], security: [{ bearer: [] }] } },
        // Wave 21: Affiliate Hooks
        '/v1/affiliate-hooks/hooks/signup': { post: { summary: 'Internal signup referral hook', tags: ['Affiliate Hooks'] } },
        '/v1/affiliate-hooks/hooks/payment': { post: { summary: 'Internal payment commission hook', tags: ['Affiliate Hooks'] } },
        '/v1/affiliate-hooks/partner/earnings': { get: { summary: 'Partner earnings dashboard', tags: ['Affiliate Hooks'], security: [{ bearer: [] }] } },
        '/v1/affiliate-hooks/partner/payout': { post: { summary: 'Request payout', tags: ['Affiliate Hooks'], security: [{ bearer: [] }] } },
        // Wave 21: Tenant Portal
        '/v1/portal/overview': { get: { summary: 'Account overview', tags: ['Portal'], security: [{ bearer: [] }] } },
        '/v1/portal/usage': { get: { summary: 'Usage summary', tags: ['Portal'], security: [{ bearer: [] }] } },
        '/v1/portal/billing': { get: { summary: 'Billing history', tags: ['Portal'], security: [{ bearer: [] }] } },
        '/v1/portal/plan': { get: { summary: 'Current plan', tags: ['Portal'], security: [{ bearer: [] }] } },
        '/v1/portal/plan/change': { post: { summary: 'Request plan change', tags: ['Portal'], security: [{ bearer: [] }] } },
        '/v1/portal/api-keys': { get: { summary: 'API keys summary', tags: ['Portal'], security: [{ bearer: [] }] } },
        '/v1/portal/notifications': { get: { summary: 'Notification settings', tags: ['Portal'], security: [{ bearer: [] }] }, put: { summary: 'Update notifications', tags: ['Portal'], security: [{ bearer: [] }] } },
        // Wave 22: GraphQL
        '/graphql': { post: { summary: 'GraphQL query endpoint', tags: ['GraphQL'], security: [{ bearer: [] }] } },
        '/graphql/schema': { get: { summary: 'GraphQL schema introspection', tags: ['GraphQL'], security: [{ bearer: [] }] } },
        // Wave 22: Advanced Analytics
        '/admin/advanced-analytics/cohorts': { get: { summary: 'Cohort analysis', tags: ['Analytics'] } },
        '/admin/advanced-analytics/retention': { get: { summary: 'Retention curve', tags: ['Analytics'] } },
        '/admin/advanced-analytics/churn-risk': { get: { summary: 'Churn risk scores', tags: ['Analytics'] } },
        '/admin/advanced-analytics/ltv': { get: { summary: 'LTV calculations', tags: ['Analytics'] } },
        '/admin/advanced-analytics/revenue': { get: { summary: 'MRR/ARR/growth metrics', tags: ['Analytics'] } },
        '/admin/advanced-analytics/heatmap': { get: { summary: 'Usage heatmap', tags: ['Analytics'] } },
        '/admin/advanced-analytics/summary': { get: { summary: 'Combined analytics dashboard', tags: ['Analytics'] } },
        // Wave 23: Event Streaming
        '/v1/events/stream': { get: { summary: 'SSE event stream', tags: ['Events'], security: [{ bearer: [] }] } },
        '/v1/events/missions/{missionId}': { get: { summary: 'SSE stream for single mission', tags: ['Events'], security: [{ bearer: [] }] } },
        '/v1/events/publish': { post: { summary: 'Publish mission event', tags: ['Events'], security: [{ bearer: [] }] } },
        '/v1/events/active': { get: { summary: 'Active stream count', tags: ['Events'], security: [{ bearer: [] }] } },
        // Wave 23: Event Bus
        '/v1/event-bus/events': { get: { summary: 'List tenant events', tags: ['EventBus'], security: [{ bearer: [] }] } },
        '/v1/event-bus/stats': { get: { summary: 'Event statistics', tags: ['EventBus'], security: [{ bearer: [] }] } },
        '/v1/event-bus/subscribe': { post: { summary: 'Subscribe to events', tags: ['EventBus'], security: [{ bearer: [] }] } },
        '/v1/event-bus/subscriptions': { get: { summary: 'List subscriptions', tags: ['EventBus'], security: [{ bearer: [] }] } },
        '/v1/event-bus/subscriptions/{id}': { delete: { summary: 'Unsubscribe', tags: ['EventBus'], security: [{ bearer: [] }] } },
        '/v1/event-bus/emit': { post: { summary: 'Emit event', tags: ['EventBus'], security: [{ bearer: [] }] } },
        // Wave 23: Webhook v2
        '/v1/webhooks-v2': { post: { summary: 'Create webhook v2', tags: ['WebhooksV2'], security: [{ bearer: [] }] }, get: { summary: 'List webhooks v2', tags: ['WebhooksV2'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v2/{id}': { get: { summary: 'Get webhook details', tags: ['WebhooksV2'], security: [{ bearer: [] }] }, put: { summary: 'Update webhook', tags: ['WebhooksV2'], security: [{ bearer: [] }] }, delete: { summary: 'Delete webhook', tags: ['WebhooksV2'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v2/{id}/deliveries': { get: { summary: 'Delivery report', tags: ['WebhooksV2'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v2/{id}/test': { post: { summary: 'Send test event', tags: ['WebhooksV2'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v2/stats': { get: { summary: 'Webhook stats', tags: ['WebhooksV2'], security: [{ bearer: [] }] } },
        // Wave 24: Rate Limiting v2
        '/v1/rate-limits/custom': { put: { summary: 'Set custom rate limits', tags: ['RateLimits'] } },
        '/v1/rate-limits/top-limited': { get: { summary: 'Top rate-limited tenants', tags: ['RateLimits'] } },
        '/v1/rate-limits/tiers': { get: { summary: 'Tier limit configs', tags: ['RateLimits'] } },
        // Wave 24: Tenant Isolation
        '/v1/isolation/status': { get: { summary: 'Isolation context', tags: ['Isolation'], security: [{ bearer: [] }] } },
        '/v1/isolation/scope': { get: { summary: 'Data scope', tags: ['Isolation'], security: [{ bearer: [] }] } },
        '/v1/isolation/score': { get: { summary: 'Isolation score', tags: ['Isolation'], security: [{ bearer: [] }] } },
        '/v1/isolation/violations': { get: { summary: 'Violation history', tags: ['Isolation'], security: [{ bearer: [] }] } },
        // Wave 24: Deep Health
        '/health/deep': { get: { summary: 'Deep health check', tags: ['System'] } },
        '/health/deep/d1': { get: { summary: 'D1 database health', tags: ['System'] } },
        '/health/deep/kv': { get: { summary: 'KV store health', tags: ['System'] } },
        '/health/deep/history': { get: { summary: 'Health history', tags: ['System'] } },
        // Wave 25: Multi-Currency
        '/v1/currencies': { get: { summary: 'Supported currencies', tags: ['Currency'] } },
        '/v1/currencies/rates': { get: { summary: 'Exchange rates', tags: ['Currency'] } },
        '/v1/currencies/convert': { post: { summary: 'Convert amount', tags: ['Currency'] } },
        '/v1/currencies/pricing': { get: { summary: 'Pricing in currency', tags: ['Currency'] } },
        '/v1/currencies/preference': { get: { summary: 'Tenant currency preference', tags: ['Currency'], security: [{ bearer: [] }] }, put: { summary: 'Set currency preference', tags: ['Currency'], security: [{ bearer: [] }] } },
        // Wave 25: Audit Export
        '/v1/audit/export': { post: { summary: 'Export audit logs', tags: ['Audit'], security: [{ bearer: [] }] } },
        '/v1/audit/compliance': { get: { summary: 'Compliance checklist', tags: ['Audit'], security: [{ bearer: [] }] } },
        '/v1/audit/retention': { get: { summary: 'Data retention policy', tags: ['Audit'], security: [{ bearer: [] }] }, put: { summary: 'Set retention policy', tags: ['Audit'], security: [{ bearer: [] }] } },
        '/v1/audit/purge': { post: { summary: 'Purge expired data', tags: ['Audit'], security: [{ bearer: [] }] } },
        '/v1/audit/gdpr-export': { get: { summary: 'GDPR data export', tags: ['Audit'], security: [{ bearer: [] }] } },
        '/v1/audit/deletion-request': { post: { summary: 'Request data deletion', tags: ['Audit'], security: [{ bearer: [] }] } },
        '/v1/audit/exports': { get: { summary: 'Export history', tags: ['Audit'], security: [{ bearer: [] }] } },
        // Wave 25: White-Label
        '/v1/branding': { get: { summary: 'Get branding config', tags: ['Branding'], security: [{ bearer: [] }] }, put: { summary: 'Update branding', tags: ['Branding'], security: [{ bearer: [] }] }, delete: { summary: 'Reset branding', tags: ['Branding'], security: [{ bearer: [] }] } },
        '/v1/branding/features': { get: { summary: 'Available branding features', tags: ['Branding'], security: [{ bearer: [] }] } },
        '/v1/branding/preview': { get: { summary: 'Preview branding CSS', tags: ['Branding'], security: [{ bearer: [] }] } },
        '/v1/branding/domain/{domain}': { get: { summary: 'Lookup branding by domain', tags: ['Branding'] } },
        // Wave 26: API Versioning
        '/api/versions': { get: { summary: 'List API versions', tags: ['Versioning'] } },
        '/api/versions/{version}': { get: { summary: 'Version details', tags: ['Versioning'] } },
        '/api/versions/{version}/changelog': { get: { summary: 'Version changelog', tags: ['Versioning'] }, post: { summary: 'Add changelog entry', tags: ['Versioning'] } },
        '/api/versions/usage': { get: { summary: 'Version usage stats', tags: ['Versioning'] } },
        '/api/versions/migrate/{from}/{to}': { get: { summary: 'Migration guide', tags: ['Versioning'] } },
        // Wave 26: Bulk Operations
        '/v1/bulk/export': { post: { summary: 'Bulk export', tags: ['Bulk'], security: [{ bearer: [] }] } },
        '/v1/bulk/import': { post: { summary: 'Bulk import', tags: ['Bulk'], security: [{ bearer: [] }] } },
        '/v1/bulk/jobs': { get: { summary: 'List bulk jobs', tags: ['Bulk'], security: [{ bearer: [] }] } },
        '/v1/bulk/jobs/{id}': { get: { summary: 'Get bulk job', tags: ['Bulk'], security: [{ bearer: [] }] } },
        '/v1/bulk/jobs/{id}/cancel': { post: { summary: 'Cancel bulk job', tags: ['Bulk'], security: [{ bearer: [] }] } },
        '/v1/bulk/stats': { get: { summary: 'Bulk operation stats', tags: ['Bulk'], security: [{ bearer: [] }] } },
        // Wave 26: SLA Monitoring
        '/sla/targets': { get: { summary: 'SLA targets by tier', tags: ['SLA'] } },
        '/sla/status': { get: { summary: 'Platform status', tags: ['SLA'] } },
        '/sla/uptime': { get: { summary: 'Uptime percentage', tags: ['SLA'] } },
        '/sla/report': { get: { summary: 'SLA compliance report', tags: ['SLA'], security: [{ bearer: [] }] } },
        '/sla/breaches': { get: { summary: 'SLA breach history', tags: ['SLA'] } },
        '/sla/history': { get: { summary: 'Uptime check history', tags: ['SLA'] } },
        // Wave 27: Notifications
        '/v1/notifications': { get: { summary: 'List notifications', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/send': { post: { summary: 'Send notification', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/unread-count': { get: { summary: 'Unread count', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/{id}/read': { put: { summary: 'Mark as read', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/read-all': { put: { summary: 'Mark all read', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/templates': { post: { summary: 'Create template', tags: ['Notifications'], security: [{ bearer: [] }] }, get: { summary: 'List templates', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/templates/{id}/send': { post: { summary: 'Send from template', tags: ['Notifications'], security: [{ bearer: [] }] } },
        '/v1/notifications/preferences/{channel}': { put: { summary: 'Update channel preference', tags: ['Notifications'], security: [{ bearer: [] }] } },
        // Wave 27: Workflows
        '/v1/workflows': { post: { summary: 'Create workflow', tags: ['Workflows'], security: [{ bearer: [] }] }, get: { summary: 'List workflows', tags: ['Workflows'], security: [{ bearer: [] }] } },
        '/v1/workflows/stats': { get: { summary: 'Workflow stats', tags: ['Workflows'], security: [{ bearer: [] }] } },
        '/v1/workflows/{id}': { get: { summary: 'Get workflow', tags: ['Workflows'], security: [{ bearer: [] }] }, put: { summary: 'Update workflow', tags: ['Workflows'], security: [{ bearer: [] }] }, delete: { summary: 'Delete workflow', tags: ['Workflows'], security: [{ bearer: [] }] } },
        '/v1/workflows/{id}/execute': { post: { summary: 'Execute workflow', tags: ['Workflows'], security: [{ bearer: [] }] } },
        '/v1/workflows/{id}/executions': { get: { summary: 'List executions', tags: ['Workflows'], security: [{ bearer: [] }] } },
        '/v1/workflows/executions/{executionId}': { get: { summary: 'Get execution', tags: ['Workflows'], security: [{ bearer: [] }] } },
        '/v1/workflows/executions/{executionId}/cancel': { post: { summary: 'Cancel execution', tags: ['Workflows'], security: [{ bearer: [] }] } },
        // Wave 27: Integration Hub
        '/v1/integrations/catalog': { get: { summary: 'Integration catalog', tags: ['Integrations'] } },
        '/v1/integrations/catalog/{slug}': { get: { summary: 'Catalog item', tags: ['Integrations'] } },
        '/v1/integrations/catalog/seed': { post: { summary: 'Seed catalog', tags: ['Integrations'] } },
        '/v1/integrations': { get: { summary: 'Installed integrations', tags: ['Integrations'], security: [{ bearer: [] }] } },
        '/v1/integrations/install': { post: { summary: 'Install integration', tags: ['Integrations'], security: [{ bearer: [] }] } },
        '/v1/integrations/{id}': { get: { summary: 'Integration detail', tags: ['Integrations'], security: [{ bearer: [] }] }, put: { summary: 'Update integration', tags: ['Integrations'], security: [{ bearer: [] }] }, delete: { summary: 'Uninstall', tags: ['Integrations'], security: [{ bearer: [] }] } },
        '/v1/integrations/{id}/events': { get: { summary: 'Integration events', tags: ['Integrations'], security: [{ bearer: [] }] } },
        '/v1/integrations/events': { get: { summary: 'All events', tags: ['Integrations'], security: [{ bearer: [] }] } },
        // Wave 28: Feature Flags
        '/v1/feature-flags': { get: { summary: 'List flags', tags: ['Feature Flags'] }, post: { summary: 'Create flag', tags: ['Feature Flags'] } },
        '/v1/feature-flags/evaluate': { get: { summary: 'Evaluate all flags', tags: ['Feature Flags'], security: [{ bearer: [] }] } },
        '/v1/feature-flags/evaluate/{key}': { get: { summary: 'Evaluate single flag', tags: ['Feature Flags'], security: [{ bearer: [] }] } },
        '/v1/feature-flags/{key}': { get: { summary: 'Flag details', tags: ['Feature Flags'] }, put: { summary: 'Update flag', tags: ['Feature Flags'] }, delete: { summary: 'Delete flag', tags: ['Feature Flags'] } },
        '/v1/feature-flags/{key}/override/{tenantId}': { put: { summary: 'Set tenant override', tags: ['Feature Flags'] }, delete: { summary: 'Remove override', tags: ['Feature Flags'] } },
        '/v1/feature-flags/{key}/stats': { get: { summary: 'Flag stats', tags: ['Feature Flags'] } },
        // Wave 28: Customer Portal
        '/v1/customer-portal/overview': { get: { summary: 'Portal overview', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/usage': { get: { summary: 'Usage summary', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/account': { get: { summary: 'Account settings', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/tickets': { post: { summary: 'Create ticket', tags: ['Customer Portal'], security: [{ bearer: [] }] }, get: { summary: 'List tickets', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/tickets/{id}': { get: { summary: 'Ticket detail', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/tickets/{id}/messages': { post: { summary: 'Add ticket message', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/tickets/{id}/status': { put: { summary: 'Update ticket status', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/activity': { get: { summary: 'Activity log', tags: ['Customer Portal'], security: [{ bearer: [] }] } },
        '/v1/customer-portal/invoices': { get: { summary: 'List invoices', tags: ['Customer Portal'], security: [{ bearer: [] }] } },

        // Wave 29: RBAC
        '/v1/rbac/roles': { get: { summary: 'List roles', tags: ['RBAC'], security: [{ bearer: [] }] }, post: { summary: 'Create role', tags: ['RBAC'], security: [{ bearer: [] }] } },
        '/v1/rbac/roles/seed': { post: { summary: 'Seed default roles', tags: ['RBAC'], security: [{ bearer: [] }] } },
        '/v1/rbac/roles/{id}': { get: { summary: 'Get role', tags: ['RBAC'], security: [{ bearer: [] }] }, put: { summary: 'Update role', tags: ['RBAC'], security: [{ bearer: [] }] }, delete: { summary: 'Delete role', tags: ['RBAC'], security: [{ bearer: [] }] } },
        '/v1/rbac/users/{userId}/roles': { get: { summary: 'Get user roles', tags: ['RBAC'], security: [{ bearer: [] }] }, post: { summary: 'Assign role', tags: ['RBAC'], security: [{ bearer: [] }] } },
        '/v1/rbac/users/{userId}/roles/{roleId}': { delete: { summary: 'Revoke role', tags: ['RBAC'], security: [{ bearer: [] }] } },
        '/v1/rbac/check': { get: { summary: 'Check permission', tags: ['RBAC'], security: [{ bearer: [] }] } },

        // Wave 29: Scheduled Missions
        '/v1/scheduled-missions': { get: { summary: 'List scheduled missions', tags: ['Scheduled Missions'], security: [{ bearer: [] }] }, post: { summary: 'Create scheduled mission', tags: ['Scheduled Missions'], security: [{ bearer: [] }] } },
        '/v1/scheduled-missions/due': { get: { summary: 'Get due missions', tags: ['Scheduled Missions'], security: [{ apiKey: [] }] } },
        '/v1/scheduled-missions/{id}': { get: { summary: 'Get scheduled mission', tags: ['Scheduled Missions'], security: [{ bearer: [] }] }, put: { summary: 'Update', tags: ['Scheduled Missions'], security: [{ bearer: [] }] }, delete: { summary: 'Delete', tags: ['Scheduled Missions'], security: [{ bearer: [] }] } },
        '/v1/scheduled-missions/{id}/pause': { post: { summary: 'Pause mission', tags: ['Scheduled Missions'], security: [{ bearer: [] }] } },
        '/v1/scheduled-missions/{id}/resume': { post: { summary: 'Resume mission', tags: ['Scheduled Missions'], security: [{ bearer: [] }] } },
        '/v1/scheduled-missions/{id}/runs': { get: { summary: 'Run history', tags: ['Scheduled Missions'], security: [{ bearer: [] }] } },

        // Wave 29: Environments
        '/v1/environments': { get: { summary: 'List environments', tags: ['Environments'], security: [{ bearer: [] }] }, post: { summary: 'Create environment', tags: ['Environments'], security: [{ bearer: [] }] } },
        '/v1/environments/seed': { post: { summary: 'Seed defaults', tags: ['Environments'], security: [{ bearer: [] }] } },
        '/v1/environments/{id}': { get: { summary: 'Get environment', tags: ['Environments'], security: [{ bearer: [] }] }, put: { summary: 'Update', tags: ['Environments'], security: [{ bearer: [] }] }, delete: { summary: 'Delete', tags: ['Environments'], security: [{ bearer: [] }] } },
        '/v1/environments/{id}/clone': { post: { summary: 'Clone environment', tags: ['Environments'], security: [{ bearer: [] }] } },
        '/v1/environments/{id}/variables': { get: { summary: 'List variables', tags: ['Environments'], security: [{ bearer: [] }] } },
        '/v1/environments/{id}/variables/{key}': { put: { summary: 'Set variable', tags: ['Environments'], security: [{ bearer: [] }] }, delete: { summary: 'Delete variable', tags: ['Environments'], security: [{ bearer: [] }] } },

        // Wave 30: Marketplace Payments
        '/v1/marketplace-payments/sellers/register': { post: { summary: 'Register as seller', tags: ['Marketplace Payments'], security: [{ bearer: [] }] } },
        '/v1/marketplace-payments/sellers/me': { get: { summary: 'My seller profile', tags: ['Marketplace Payments'], security: [{ bearer: [] }] }, put: { summary: 'Update profile', tags: ['Marketplace Payments'], security: [{ bearer: [] }] } },
        '/v1/marketplace-payments/sellers/me/transactions': { get: { summary: 'My transactions', tags: ['Marketplace Payments'], security: [{ bearer: [] }] } },
        '/v1/marketplace-payments/sellers/me/earnings': { get: { summary: 'My earnings', tags: ['Marketplace Payments'], security: [{ bearer: [] }] } },
        '/v1/marketplace-payments/sellers/me/payouts': { get: { summary: 'Payout history', tags: ['Marketplace Payments'], security: [{ bearer: [] }] }, post: { summary: 'Request payout', tags: ['Marketplace Payments'], security: [{ bearer: [] }] } },
        '/v1/marketplace-payments/purchase': { post: { summary: 'Record purchase', tags: ['Marketplace Payments'], security: [{ bearer: [] }] } },

        // Wave 30: Platform KPIs
        '/admin/kpis/overview': { get: { summary: 'KPI overview', tags: ['Platform KPIs'], security: [{ apiKey: [] }] } },
        '/admin/kpis/revenue': { get: { summary: 'Revenue metrics', tags: ['Platform KPIs'], security: [{ apiKey: [] }] } },
        '/admin/kpis/tenants': { get: { summary: 'Tenant metrics', tags: ['Platform KPIs'], security: [{ apiKey: [] }] } },
        '/admin/kpis/churn': { get: { summary: 'Churn rate', tags: ['Platform KPIs'], security: [{ apiKey: [] }] } },
        '/admin/kpis/top-tenants': { get: { summary: 'Top tenants', tags: ['Platform KPIs'], security: [{ apiKey: [] }] } },
        '/admin/kpis/snapshot': { post: { summary: 'Take KPI snapshot', tags: ['Platform KPIs'], security: [{ apiKey: [] }] } },

        // Wave 30: Pricing Plans
        '/v1/pricing/plans': { get: { summary: 'List plans', tags: ['Pricing'] }, post: { summary: 'Create plan', tags: ['Pricing'], security: [{ apiKey: [] }] } },
        '/v1/pricing/plans/seed': { post: { summary: 'Seed default plans', tags: ['Pricing'], security: [{ apiKey: [] }] } },
        '/v1/pricing/plans/{id}': { get: { summary: 'Get plan', tags: ['Pricing'] }, put: { summary: 'Update plan', tags: ['Pricing'], security: [{ apiKey: [] }] }, delete: { summary: 'Delete plan', tags: ['Pricing'], security: [{ apiKey: [] }] } },
        '/v1/pricing/subscription': { get: { summary: 'My subscription', tags: ['Pricing'], security: [{ bearer: [] }] } },
        '/v1/pricing/subscribe': { post: { summary: 'Subscribe to plan', tags: ['Pricing'], security: [{ bearer: [] }] } },
        '/v1/pricing/cancel': { post: { summary: 'Cancel subscription', tags: ['Pricing'], security: [{ bearer: [] }] } },
        '/v1/pricing/check-access': { get: { summary: 'Check feature access', tags: ['Pricing'], security: [{ bearer: [] }] } },
        '/v1/pricing/check-limit': { get: { summary: 'Check plan limit', tags: ['Pricing'], security: [{ bearer: [] }] } },
        // Wave 31: Audit Streaming
        '/v1/audit-streaming/configs': { get: { summary: 'List stream configs', tags: ['Audit Streaming'], security: [{ bearer: [] }] }, post: { summary: 'Create stream config', tags: ['Audit Streaming'], security: [{ bearer: [] }] } },
        '/v1/audit-streaming/configs/{id}': { put: { summary: 'Update stream config', tags: ['Audit Streaming'], security: [{ bearer: [] }] }, delete: { summary: 'Delete stream config', tags: ['Audit Streaming'], security: [{ bearer: [] }] } },
        '/v1/audit-streaming/stats': { get: { summary: 'Delivery statistics', tags: ['Audit Streaming'], security: [{ bearer: [] }] } },
        '/v1/audit-streaming/publish': { post: { summary: 'Publish audit event', tags: ['Audit Streaming'], security: [{ bearer: [] }] } },
        // Wave 31: IP Allowlist
        '/v1/ip-allowlist/rules': { get: { summary: 'List IP rules', tags: ['IP Allowlist'], security: [{ bearer: [] }] }, post: { summary: 'Add IP rule', tags: ['IP Allowlist'], security: [{ bearer: [] }] } },
        '/v1/ip-allowlist/rules/{id}': { put: { summary: 'Update IP rule', tags: ['IP Allowlist'], security: [{ bearer: [] }] }, delete: { summary: 'Delete IP rule', tags: ['IP Allowlist'], security: [{ bearer: [] }] } },
        '/v1/ip-allowlist/check': { post: { summary: 'Check IP allowed', tags: ['IP Allowlist'], security: [{ bearer: [] }] } },
        '/v1/ip-allowlist/logs': { get: { summary: 'Access logs', tags: ['IP Allowlist'], security: [{ bearer: [] }] } },
        // Wave 31: Data Retention
        '/v1/data-retention/policies': { get: { summary: 'List retention policies', tags: ['Data Retention'], security: [{ bearer: [] }] }, post: { summary: 'Create retention policy', tags: ['Data Retention'], security: [{ bearer: [] }] } },
        '/v1/data-retention/policies/{id}': { put: { summary: 'Update policy', tags: ['Data Retention'], security: [{ bearer: [] }] }, delete: { summary: 'Delete policy', tags: ['Data Retention'], security: [{ bearer: [] }] } },
        '/v1/data-retention/stats': { get: { summary: 'Retention impact stats', tags: ['Data Retention'], security: [{ bearer: [] }] } },
        '/v1/data-retention/purge/{id}': { post: { summary: 'Manual purge', tags: ['Data Retention'], security: [{ bearer: [] }] } },
        '/v1/data-retention/seed': { post: { summary: 'Seed default policies', tags: ['Data Retention'], security: [{ bearer: [] }] } },
        // Wave 32: Error Budgets
        '/v1/error-budgets/slos': { get: { summary: 'List SLOs', tags: ['Error Budgets'], security: [{ bearer: [] }] }, post: { summary: 'Create SLO', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        '/v1/error-budgets/slos/{id}': { put: { summary: 'Update SLO', tags: ['Error Budgets'], security: [{ bearer: [] }] }, delete: { summary: 'Delete SLO', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        '/v1/error-budgets/summary': { get: { summary: 'Error budget summary', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        '/v1/error-budgets/slos/{id}/budget': { get: { summary: 'SLO budget details', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        '/v1/error-budgets/slos/{id}/measure': { post: { summary: 'Record SLI measurement', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        '/v1/error-budgets/alerts': { get: { summary: 'Budget alerts', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        '/v1/error-budgets/seed': { post: { summary: 'Seed default SLOs', tags: ['Error Budgets'], security: [{ bearer: [] }] } },
        // Wave 32: Usage Forecasting
        '/v1/usage-forecast/snapshots': { get: { summary: 'Historical snapshots', tags: ['Usage Forecast'], security: [{ bearer: [] }] }, post: { summary: 'Record snapshot', tags: ['Usage Forecast'], security: [{ bearer: [] }] } },
        '/v1/usage-forecast/generate': { post: { summary: 'Generate forecast', tags: ['Usage Forecast'], security: [{ bearer: [] }] } },
        '/v1/usage-forecast/forecast': { get: { summary: 'Get forecast', tags: ['Usage Forecast'], security: [{ bearer: [] }] } },
        '/v1/usage-forecast/all': { get: { summary: 'All metric forecasts', tags: ['Usage Forecast'], security: [{ bearer: [] }] } },
        '/v1/usage-forecast/anomalies': { get: { summary: 'Detect anomalies', tags: ['Usage Forecast'], security: [{ bearer: [] }] } },
        '/v1/usage-forecast/capacity-alert': { get: { summary: 'Capacity alerts', tags: ['Usage Forecast'], security: [{ bearer: [] }] } },
        // Wave 32: Compliance Reports
        '/v1/compliance/reports': { get: { summary: 'List compliance reports', tags: ['Compliance'], security: [{ bearer: [] }] } },
        '/v1/compliance/reports/generate': { post: { summary: 'Generate compliance report', tags: ['Compliance'], security: [{ bearer: [] }] } },
        '/v1/compliance/reports/{id}': { get: { summary: 'Get report detail', tags: ['Compliance'], security: [{ bearer: [] }] }, delete: { summary: 'Delete report', tags: ['Compliance'], security: [{ bearer: [] }] } },
        '/v1/compliance/checks': { get: { summary: 'Run compliance checks', tags: ['Compliance'], security: [{ bearer: [] }] } },
        '/v1/compliance/score': { get: { summary: 'Compliance score', tags: ['Compliance'], security: [{ bearer: [] }] } },
        '/v1/compliance/summary': { get: { summary: 'Cross-category summary', tags: ['Compliance'], security: [{ bearer: [] }] } },
        '/v1/compliance/frameworks': { get: { summary: 'Supported frameworks', tags: ['Compliance'] } },
        // Wave 33: Cron Orchestrator
        '/v1/cron/jobs': { get: { summary: 'List cron jobs', tags: ['Cron'], security: [{ bearer: [] }] }, post: { summary: 'Register cron job', tags: ['Cron'], security: [{ bearer: [] }] } },
        '/v1/cron/stats': { get: { summary: 'Cron job stats', tags: ['Cron'], security: [{ bearer: [] }] } },
        '/v1/cron/seed': { post: { summary: 'Seed system jobs', tags: ['Cron'], security: [{ bearer: [] }] } },
        '/v1/cron/jobs/{id}/status': { put: { summary: 'Update job status', tags: ['Cron'], security: [{ bearer: [] }] } },
        '/v1/cron/jobs/{id}/logs': { get: { summary: 'Job execution logs', tags: ['Cron'], security: [{ bearer: [] }] } },
        '/v1/cron/admin/overdue': { get: { summary: 'Overdue jobs', tags: ['Cron'] } },
        '/v1/cron/admin/run': { post: { summary: 'Run all overdue', tags: ['Cron'] } },
        // Wave 33: Onboarding V2
        '/v1/onboarding-v2/status': { get: { summary: 'Onboarding status', tags: ['Onboarding V2'], security: [{ bearer: [] }] } },
        '/v1/onboarding-v2/start': { post: { summary: 'Start onboarding', tags: ['Onboarding V2'], security: [{ bearer: [] }] } },
        '/v1/onboarding-v2/complete/{step}': { post: { summary: 'Complete step', tags: ['Onboarding V2'], security: [{ bearer: [] }] } },
        '/v1/onboarding-v2/skip/{step}': { post: { summary: 'Skip step', tags: ['Onboarding V2'], security: [{ bearer: [] }] } },
        '/v1/onboarding-v2/recommendations': { get: { summary: 'Recommendations', tags: ['Onboarding V2'], security: [{ bearer: [] }] } },
        '/v1/onboarding-v2/seed-defaults': { post: { summary: 'Seed defaults', tags: ['Onboarding V2'], security: [{ bearer: [] }] } },
        // Wave 33: Platform Health
        '/platform-health/overview': { get: { summary: 'Platform overview', tags: ['Platform Health'] } },
        '/platform-health/services': { get: { summary: 'Service statuses', tags: ['Platform Health'] } },
        '/platform-health/features': { get: { summary: 'Feature coverage', tags: ['Platform Health'] } },
        '/platform-health/endpoints': { get: { summary: 'API endpoint count', tags: ['Platform Health'] } },
        '/platform-health/degraded': { get: { summary: 'Degraded services', tags: ['Platform Health'] } },
        '/platform-health/capacity': { get: { summary: 'System capacity', tags: ['Platform Health'] } },
        // Wave 34: Revenue Analytics V2
        '/admin/revenue-v2/mrr': { get: { summary: 'MRR breakdown', tags: ['Revenue V2'] } },
        '/admin/revenue-v2/cohorts': { get: { summary: 'Cohort analysis', tags: ['Revenue V2'] } },
        '/admin/revenue-v2/nrr': { get: { summary: 'Net revenue retention', tags: ['Revenue V2'] } },
        '/admin/revenue-v2/segments': { get: { summary: 'Customer segments', tags: ['Revenue V2'] } },
        '/admin/revenue-v2/expansion': { get: { summary: 'Expansion revenue', tags: ['Revenue V2'] } },
        '/admin/revenue-v2/top-tenants': { get: { summary: 'Top revenue tenants', tags: ['Revenue V2'] } },
        '/admin/revenue-v2/forecast': { get: { summary: 'Revenue forecast', tags: ['Revenue V2'] } },
        // Wave 34: Tenant Lifecycle
        '/v1/lifecycle/stage': { get: { summary: 'Lifecycle stage', tags: ['Lifecycle'], security: [{ bearer: [] }] } },
        '/v1/lifecycle/history': { get: { summary: 'Transition history', tags: ['Lifecycle'], security: [{ bearer: [] }] } },
        '/v1/lifecycle/risk': { get: { summary: 'Risk score', tags: ['Lifecycle'], security: [{ bearer: [] }] } },
        '/v1/lifecycle/admin/at-risk': { get: { summary: 'At-risk tenants', tags: ['Lifecycle'] } },
        '/v1/lifecycle/admin/distribution': { get: { summary: 'Stage distribution', tags: ['Lifecycle'] } },
        '/v1/lifecycle/admin/churn': { get: { summary: 'Churn analysis', tags: ['Lifecycle'] } },
        '/v1/lifecycle/admin/evaluate': { post: { summary: 'Auto transitions', tags: ['Lifecycle'] } },
        // Wave 34: Adaptive Rate Limiting
        '/v1/adaptive-rate-limit/config': { get: { summary: 'Rate limit config', tags: ['Rate Limit V2'], security: [{ bearer: [] }] }, post: { summary: 'Set rate limit', tags: ['Rate Limit V2'], security: [{ bearer: [] }] } },
        '/v1/adaptive-rate-limit/violations': { get: { summary: 'Violation history', tags: ['Rate Limit V2'], security: [{ bearer: [] }] } },
        '/v1/adaptive-rate-limit/status': { get: { summary: 'Rate limit status', tags: ['Rate Limit V2'], security: [{ bearer: [] }] } },
        '/v1/adaptive-rate-limit/admin/violators': { get: { summary: 'Top violators', tags: ['Rate Limit V2'] } },
        '/v1/adaptive-rate-limit/admin/seed': { post: { summary: 'Seed tier defaults', tags: ['Rate Limit V2'] } },
        '/v1/adaptive-rate-limit/admin/tier-defaults': { get: { summary: 'Tier defaults', tags: ['Rate Limit V2'] } },
        // Wave 35: API Sandbox
        '/v1/sandbox/environments': { get: { summary: 'List sandboxes', tags: ['Sandbox'], security: [{ bearer: [] }] }, post: { summary: 'Create sandbox', tags: ['Sandbox'], security: [{ bearer: [] }] } },
        '/v1/sandbox/stats': { get: { summary: 'Sandbox stats', tags: ['Sandbox'], security: [{ bearer: [] }] } },
        '/v1/sandbox/execute': { post: { summary: 'Execute sandbox request', tags: ['Sandbox'], security: [{ bearer: [] }] } },
        '/v1/sandbox/environments/{id}': { get: { summary: 'Get sandbox', tags: ['Sandbox'], security: [{ bearer: [] }] }, delete: { summary: 'Delete sandbox', tags: ['Sandbox'], security: [{ bearer: [] }] } },
        '/v1/sandbox/environments/{id}/mock': { post: { summary: 'Set mock response', tags: ['Sandbox'], security: [{ bearer: [] }] } },
        '/v1/sandbox/environments/{id}/history': { get: { summary: 'Request history', tags: ['Sandbox'], security: [{ bearer: [] }] } },
        // Wave 35: Webhook Simulator
        '/v1/webhook-simulator/simulate': { post: { summary: 'Simulate webhook', tags: ['Webhook Sim'], security: [{ bearer: [] }] } },
        '/v1/webhook-simulator/simulations': { get: { summary: 'List simulations', tags: ['Webhook Sim'], security: [{ bearer: [] }] } },
        '/v1/webhook-simulator/stats': { get: { summary: 'Simulation stats', tags: ['Webhook Sim'], security: [{ bearer: [] }] } },
        '/v1/webhook-simulator/sample/{eventType}': { get: { summary: 'Sample payload', tags: ['Webhook Sim'], security: [{ bearer: [] }] } },
        '/v1/webhook-simulator/simulations/{id}': { get: { summary: 'Get simulation', tags: ['Webhook Sim'], security: [{ bearer: [] }] } },
        '/v1/webhook-simulator/test-endpoints': { get: { summary: 'List test endpoints', tags: ['Webhook Sim'], security: [{ bearer: [] }] }, post: { summary: 'Create test endpoint', tags: ['Webhook Sim'], security: [{ bearer: [] }] } },
        // Wave 35: API Usage Analytics
        '/v1/api-analytics/summary': { get: { summary: 'Usage summary', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/endpoints': { get: { summary: 'Endpoint stats', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/top': { get: { summary: 'Top endpoints', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/slowest': { get: { summary: 'Slowest endpoints', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/errors': { get: { summary: 'Error breakdown', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/errors/hotspots': { get: { summary: 'Error hotspots', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/trend/latency': { get: { summary: 'Latency trend', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        '/v1/api-analytics/trend/volume': { get: { summary: 'Volume trend', tags: ['API Analytics'], security: [{ bearer: [] }] } },
        // Wave 36: Tenant Backup
        '/v1/backup/backups': { get: { summary: 'List backups', tags: ['Backup'], security: [{ bearer: [] }] }, post: { summary: 'Create backup', tags: ['Backup'], security: [{ bearer: [] }] } },
        '/v1/backup/stats': { get: { summary: 'Backup stats', tags: ['Backup'], security: [{ bearer: [] }] } },
        '/v1/backup/backups/{id}': { get: { summary: 'Get backup', tags: ['Backup'], security: [{ bearer: [] }] }, delete: { summary: 'Delete backup', tags: ['Backup'], security: [{ bearer: [] }] } },
        '/v1/backup/backups/{id}/download': { get: { summary: 'Download backup', tags: ['Backup'], security: [{ bearer: [] }] } },
        '/v1/backup/backups/{id}/restore': { post: { summary: 'Restore backup', tags: ['Backup'], security: [{ bearer: [] }] } },
        // Wave 36: Multi-Region
        '/v1/region/config': { get: { summary: 'Region config', tags: ['Region'], security: [{ bearer: [] }] }, put: { summary: 'Set region', tags: ['Region'], security: [{ bearer: [] }] } },
        '/v1/region/optimal': { get: { summary: 'Optimal region', tags: ['Region'], security: [{ bearer: [] }] } },
        '/v1/region/regions': { get: { summary: 'Available regions', tags: ['Region'] } },
        '/v1/region/status': { get: { summary: 'Region status', tags: ['Region'] } },
        '/v1/region/admin/seed': { post: { summary: 'Seed regions', tags: ['Region'] } },
        '/v1/region/admin/stats': { get: { summary: 'Region stats', tags: ['Region'] } },
        // Wave 36: Platform Audit Trail
        '/admin/audit-trail/stats': { get: { summary: 'Audit stats', tags: ['Audit Trail'] } },
        '/admin/audit-trail/actor/{actorId}': { get: { summary: 'Actor history', tags: ['Audit Trail'] } },
        '/admin/audit-trail/resource/{type}/{id}': { get: { summary: 'Resource history', tags: ['Audit Trail'] } },
        '/admin/audit-trail/search': { get: { summary: 'Search audit', tags: ['Audit Trail'] } },
        '/admin/audit-trail/export': { get: { summary: 'Export audit', tags: ['Audit Trail'] } },
        '/admin/audit-trail/retention': { get: { summary: 'Retention configs', tags: ['Audit Trail'] }, post: { summary: 'Set retention', tags: ['Audit Trail'] } },
        // Wave 37: Custom Domains
        '/v1/custom-domains/domains': { get: { summary: 'List custom domains', tags: ['Custom Domains'], security: [{ bearer: [] }] }, post: { summary: 'Add custom domain', tags: ['Custom Domains'], security: [{ bearer: [] }] } },
        '/v1/custom-domains/domains/{id}': { get: { summary: 'Get domain detail', tags: ['Custom Domains'], security: [{ bearer: [] }] }, delete: { summary: 'Remove domain', tags: ['Custom Domains'], security: [{ bearer: [] }] } },
        '/v1/custom-domains/domains/{id}/verify': { post: { summary: 'Verify domain', tags: ['Custom Domains'], security: [{ bearer: [] }] } },
        '/v1/custom-domains/stats': { get: { summary: 'Domain stats', tags: ['Custom Domains'], security: [{ bearer: [] }] } },
        '/v1/custom-domains/lookup/{hostname}': { get: { summary: 'Lookup tenant by hostname', tags: ['Custom Domains'] } },
        '/v1/custom-domains/admin/overview': { get: { summary: 'All domains overview', tags: ['Custom Domains'] } },
        // Wave 37: Tenant Collaboration
        '/v1/collaboration/comments/{missionId}': { get: { summary: 'List comments', tags: ['Collaboration'], security: [{ bearer: [] }] }, post: { summary: 'Add comment', tags: ['Collaboration'], security: [{ bearer: [] }] } },
        '/v1/collaboration/comments/{commentId}': { delete: { summary: 'Delete comment', tags: ['Collaboration'], security: [{ bearer: [] }] } },
        '/v1/collaboration/views': { get: { summary: 'List shared views', tags: ['Collaboration'], security: [{ bearer: [] }] }, post: { summary: 'Create shared view', tags: ['Collaboration'], security: [{ bearer: [] }] } },
        '/v1/collaboration/views/{viewId}': { delete: { summary: 'Delete shared view', tags: ['Collaboration'], security: [{ bearer: [] }] } },
        '/v1/collaboration/feed': { get: { summary: 'Activity feed', tags: ['Collaboration'], security: [{ bearer: [] }] } },
        '/v1/collaboration/stats': { get: { summary: 'Collaboration stats', tags: ['Collaboration'], security: [{ bearer: [] }] } },
        // Wave 37: AI Agent Marketplace
        '/v1/agent-marketplace/browse': { get: { summary: 'Browse agents', tags: ['Agent Marketplace'] } },
        '/v1/agent-marketplace/featured': { get: { summary: 'Featured agents', tags: ['Agent Marketplace'] } },
        '/v1/agent-marketplace/agent/{slug}': { get: { summary: 'Agent detail', tags: ['Agent Marketplace'] } },
        '/v1/agent-marketplace/agent/{slug}/reviews': { get: { summary: 'Agent reviews', tags: ['Agent Marketplace'] } },
        '/v1/agent-marketplace/install/{agentId}': { post: { summary: 'Install agent', tags: ['Agent Marketplace'], security: [{ bearer: [] }] }, delete: { summary: 'Uninstall agent', tags: ['Agent Marketplace'], security: [{ bearer: [] }] } },
        '/v1/agent-marketplace/installed': { get: { summary: 'Installed agents', tags: ['Agent Marketplace'], security: [{ bearer: [] }] } },
        '/v1/agent-marketplace/publish': { post: { summary: 'Publish agent', tags: ['Agent Marketplace'], security: [{ bearer: [] }] } },
        '/v1/agent-marketplace/publisher/stats': { get: { summary: 'Publisher stats', tags: ['Agent Marketplace'], security: [{ bearer: [] }] } },
        '/v1/agent-marketplace/admin/stats': { get: { summary: 'Marketplace overview', tags: ['Agent Marketplace'] } },
        // Wave 38: Usage Alerts
        '/v1/usage-alerts/rules': { get: { summary: 'List alert rules', tags: ['Usage Alerts'], security: [{ bearer: [] }] }, post: { summary: 'Create alert rule', tags: ['Usage Alerts'], security: [{ bearer: [] }] } },
        '/v1/usage-alerts/rules/{ruleId}': { put: { summary: 'Update rule', tags: ['Usage Alerts'], security: [{ bearer: [] }] }, delete: { summary: 'Delete rule', tags: ['Usage Alerts'], security: [{ bearer: [] }] } },
        '/v1/usage-alerts/history': { get: { summary: 'Alert history', tags: ['Usage Alerts'], security: [{ bearer: [] }] } },
        '/v1/usage-alerts/budget': { get: { summary: 'Get budget config', tags: ['Usage Alerts'], security: [{ bearer: [] }] }, put: { summary: 'Set budget config', tags: ['Usage Alerts'], security: [{ bearer: [] }] } },
        '/v1/usage-alerts/check': { post: { summary: 'Check budget limit', tags: ['Usage Alerts'], security: [{ bearer: [] }] } },
        '/v1/usage-alerts/admin/overview': { get: { summary: 'Alert overview', tags: ['Usage Alerts'] } },
        // Wave 38: Migration Tools
        '/v1/migration/jobs': { get: { summary: 'List migration jobs', tags: ['Migration'], security: [{ bearer: [] }] }, post: { summary: 'Create migration job', tags: ['Migration'], security: [{ bearer: [] }] } },
        '/v1/migration/jobs/{jobId}': { get: { summary: 'Job status', tags: ['Migration'], security: [{ bearer: [] }] } },
        '/v1/migration/import/{jobId}': { post: { summary: 'Upload import data', tags: ['Migration'], security: [{ bearer: [] }] } },
        '/v1/migration/export': { get: { summary: 'Export tenant data', tags: ['Migration'], security: [{ bearer: [] }] } },
        '/v1/migration/supported-platforms': { get: { summary: 'Supported platforms', tags: ['Migration'] } },
        '/v1/migration/admin/stats': { get: { summary: 'Migration statistics', tags: ['Migration'] } },
        // Wave 38: Notifications Hub
        '/v1/notifications-hub/channels': { get: { summary: 'List channels', tags: ['Notifications Hub'], security: [{ bearer: [] }] }, post: { summary: 'Add channel', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/channels/{channelId}': { put: { summary: 'Update channel', tags: ['Notifications Hub'], security: [{ bearer: [] }] }, delete: { summary: 'Remove channel', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/send': { post: { summary: 'Send notification', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/log': { get: { summary: 'Notification log', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/stats': { get: { summary: 'Notification stats', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/templates': { get: { summary: 'List templates', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/templates/{eventType}': { put: { summary: 'Upsert template', tags: ['Notifications Hub'], security: [{ bearer: [] }] } },
        '/v1/notifications-hub/admin/seed-templates': { post: { summary: 'Seed defaults', tags: ['Notifications Hub'] } },
        '/v1/notifications-hub/admin/overview': { get: { summary: 'Platform overview', tags: ['Notifications Hub'] } },
        // Wave 39: Tenant API Tokens
        '/v1/api-tokens/tokens': { get: { summary: 'List API tokens', tags: ['API Tokens'], security: [{ bearer: [] }] }, post: { summary: 'Create token', tags: ['API Tokens'], security: [{ bearer: [] }] } },
        '/v1/api-tokens/tokens/{tokenId}': { get: { summary: 'Token detail', tags: ['API Tokens'], security: [{ bearer: [] }] }, delete: { summary: 'Revoke token', tags: ['API Tokens'], security: [{ bearer: [] }] } },
        '/v1/api-tokens/tokens/{tokenId}/rotate': { post: { summary: 'Rotate token', tags: ['API Tokens'], security: [{ bearer: [] }] } },
        '/v1/api-tokens/validate': { post: { summary: 'Validate token', tags: ['API Tokens'] } },
        '/v1/api-tokens/admin/overview': { get: { summary: 'Token overview', tags: ['API Tokens'] } },
        // Wave 39: Mission Webhooks V3
        '/v1/mission-webhooks-v3/subscriptions': { get: { summary: 'List webhook subs', tags: ['Webhooks V3'], security: [{ bearer: [] }] }, post: { summary: 'Create subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/mission-webhooks-v3/subscriptions/{subId}': { get: { summary: 'Get subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] }, put: { summary: 'Update subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] }, delete: { summary: 'Delete subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/mission-webhooks-v3/deliveries': { get: { summary: 'Delivery history', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/mission-webhooks-v3/deliveries/{deliveryId}/retry': { post: { summary: 'Retry delivery', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/mission-webhooks-v3/stats': { get: { summary: 'Delivery stats', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/mission-webhooks-v3/admin/overview': { get: { summary: 'Webhook overview', tags: ['Webhooks V3'] } },
        // Wave 39: Platform Announcements
        '/v1/announcements/active': { get: { summary: 'Active announcements', tags: ['Announcements'], security: [{ bearer: [] }] } },
        '/v1/announcements/maintenance': { get: { summary: 'Maintenance windows', tags: ['Announcements'] } },
        '/v1/announcements/dismiss/{announcementId}': { post: { summary: 'Dismiss announcement', tags: ['Announcements'], security: [{ bearer: [] }] } },
        '/v1/announcements/admin/create': { post: { summary: 'Create announcement', tags: ['Announcements'] } },
        '/v1/announcements/admin/list': { get: { summary: 'List announcements', tags: ['Announcements'] } },
        '/v1/announcements/admin/stats': { get: { summary: 'Announcement stats', tags: ['Announcements'] } },
        // Wave 40: Tenant Quotas
        '/v1/quotas/quotas': { get: { summary: 'Get quotas', tags: ['Quotas'], security: [{ bearer: [] }] } },
        '/v1/quotas/usage': { get: { summary: 'Quota usage', tags: ['Quotas'], security: [{ bearer: [] }] } },
        '/v1/quotas/check': { post: { summary: 'Check quota', tags: ['Quotas'], security: [{ bearer: [] }] } },
        '/v1/quotas/history': { get: { summary: 'Quota history', tags: ['Quotas'], security: [{ bearer: [] }] } },
        '/v1/quotas/tier-defaults/{tier}': { get: { summary: 'Tier defaults', tags: ['Quotas'] } },
        '/v1/quotas/admin/overview': { get: { summary: 'Quota overview', tags: ['Quotas'] } },
        // Wave 40: AI Model Registry
        '/v1/ai-models/models': { get: { summary: 'List models', tags: ['AI Models'] } },
        '/v1/ai-models/models/{id}': { get: { summary: 'Model detail', tags: ['AI Models'] } },
        '/v1/ai-models/providers': { get: { summary: 'List providers', tags: ['AI Models'] } },
        '/v1/ai-models/usage': { get: { summary: 'Model usage', tags: ['AI Models'], security: [{ bearer: [] }] } },
        '/v1/ai-models/costs': { get: { summary: 'Cost breakdown', tags: ['AI Models'], security: [{ bearer: [] }] } },
        '/v1/ai-models/admin/providers': { post: { summary: 'Register provider', tags: ['AI Models'] } },
        '/v1/ai-models/admin/models': { post: { summary: 'Register model', tags: ['AI Models'] } },
        '/v1/ai-models/admin/top-models': { get: { summary: 'Top models', tags: ['AI Models'] } },
        '/v1/ai-models/admin/seed': { post: { summary: 'Seed models', tags: ['AI Models'] } },
        // Wave 40: Platform Metrics Dashboard
        '/admin/platform-metrics/dashboard': { get: { summary: 'Dashboard summary', tags: ['Platform Metrics'] } },
        '/admin/platform-metrics/metrics': { get: { summary: 'Current metrics', tags: ['Platform Metrics'] } },
        '/admin/platform-metrics/metrics/{metricName}': { get: { summary: 'Metric timeline', tags: ['Platform Metrics'] } },
        '/admin/platform-metrics/growth': { get: { summary: 'Tenant growth', tags: ['Platform Metrics'] } },
        '/admin/platform-metrics/revenue': { get: { summary: 'Revenue metrics', tags: ['Platform Metrics'] } },
        '/admin/platform-metrics/goals': { get: { summary: 'List goals', tags: ['Platform Metrics'] }, post: { summary: 'Create goal', tags: ['Platform Metrics'] } },
        // Wave 41: Tenant SSO V2
        '/v1/sso/configs': { get: { summary: 'List SSO configs', tags: ['SSO'] }, post: { summary: 'Create SSO config', tags: ['SSO'] } },
        '/v1/sso/configs/{configId}': { get: { summary: 'Get SSO config', tags: ['SSO'] }, put: { summary: 'Update SSO config', tags: ['SSO'] }, delete: { summary: 'Delete SSO config', tags: ['SSO'] } },
        '/v1/sso/login/{configId}': { post: { summary: 'Initiate SSO login', tags: ['SSO'] } },
        '/v1/sso/callback': { post: { summary: 'SSO callback', tags: ['SSO'] } },
        '/v1/sso/stats': { get: { summary: 'SSO stats', tags: ['SSO'] } },
        '/v1/sso/admin/overview': { get: { summary: 'Admin SSO overview', tags: ['SSO'] } },
        // Wave 41: API Gateway Caching
        '/v1/cache/configs': { get: { summary: 'List cache configs', tags: ['Caching'] }, post: { summary: 'Create cache config', tags: ['Caching'] } },
        '/v1/cache/configs/{configId}': { put: { summary: 'Update cache config', tags: ['Caching'] }, delete: { summary: 'Delete cache config', tags: ['Caching'] } },
        '/v1/cache/invalidate': { post: { summary: 'Invalidate cache', tags: ['Caching'] } },
        '/v1/cache/stats': { get: { summary: 'Cache stats', tags: ['Caching'] } },
        '/v1/cache/analytics': { get: { summary: 'Cache analytics', tags: ['Caching'] } },
        '/v1/cache/admin/overview': { get: { summary: 'Admin cache overview', tags: ['Caching'] } },
        // Wave 41: Mission Dependencies
        '/v1/mission-chains/chains': { get: { summary: 'List mission chains', tags: ['Mission Chains'] }, post: { summary: 'Create chain', tags: ['Mission Chains'] } },
        '/v1/mission-chains/chains/{chainId}': { get: { summary: 'Get chain', tags: ['Mission Chains'] } },
        '/v1/mission-chains/chains/{chainId}/missions': { post: { summary: 'Add mission to chain', tags: ['Mission Chains'] } },
        '/v1/mission-chains/chains/{chainId}/start': { post: { summary: 'Start chain', tags: ['Mission Chains'] } },
        '/v1/mission-chains/chains/{chainId}/ready': { get: { summary: 'Get ready missions', tags: ['Mission Chains'] } },
        '/v1/mission-chains/admin/overview': { get: { summary: 'Admin chains overview', tags: ['Mission Chains'] } },
        // Wave 42: Tenant Invoicing
        '/v1/invoicing/invoices': { get: { summary: 'List invoices', tags: ['Invoicing'] }, post: { summary: 'Create invoice', tags: ['Invoicing'] } },
        '/v1/invoicing/invoices/{invoiceId}': { get: { summary: 'Get invoice', tags: ['Invoicing'] } },
        '/v1/invoicing/invoices/{invoiceId}/items': { post: { summary: 'Add line item', tags: ['Invoicing'] } },
        '/v1/invoicing/invoices/{invoiceId}/status': { put: { summary: 'Update invoice status', tags: ['Invoicing'] } },
        '/v1/invoicing/summary': { get: { summary: 'Invoice summary', tags: ['Invoicing'] } },
        '/v1/invoicing/admin/overview': { get: { summary: 'Admin invoice overview', tags: ['Invoicing'] } },
        '/v1/invoicing/admin/overdue': { get: { summary: 'Overdue invoices', tags: ['Invoicing'] } },
        // Wave 42: Platform Changelog V2
        '/v1/changelog-v2/entries': { get: { summary: 'List changelog entries', tags: ['Changelog'] } },
        '/v1/changelog-v2/entries/{entryId}': { get: { summary: 'Get changelog entry', tags: ['Changelog'] } },
        '/v1/changelog-v2/unread': { get: { summary: 'Unread count', tags: ['Changelog'] } },
        '/v1/changelog-v2/subscription': { get: { summary: 'Get subscription', tags: ['Changelog'] }, post: { summary: 'Subscribe', tags: ['Changelog'] } },
        '/v1/changelog-v2/admin/entries': { post: { summary: 'Create entry', tags: ['Changelog'] } },
        '/v1/changelog-v2/admin/stats': { get: { summary: 'Changelog stats', tags: ['Changelog'] } },
        // Wave 42: Admin Command Center
        '/admin/commands/execute': { post: { summary: 'Execute command', tags: ['Command Center'] } },
        '/admin/commands/history': { get: { summary: 'Command history', tags: ['Command Center'] } },
        '/admin/commands/available': { get: { summary: 'Available commands', tags: ['Command Center'] } },
        '/admin/commands/scheduled': { get: { summary: 'List scheduled', tags: ['Command Center'] }, post: { summary: 'Create scheduled', tags: ['Command Center'] } },
        '/admin/commands/stats': { get: { summary: 'Command stats', tags: ['Command Center'] } },
        '/admin/commands/dashboard': { get: { summary: 'Dashboard summary', tags: ['Command Center'] } },
        // Wave 43: Webhook Analytics
        '/v1/webhook-analytics/stats': { get: { summary: 'Delivery stats', tags: ['Webhook Analytics'] } },
        '/v1/webhook-analytics/timeline': { get: { summary: 'Delivery timeline', tags: ['Webhook Analytics'] } },
        '/v1/webhook-analytics/endpoints': { get: { summary: 'Endpoint health', tags: ['Webhook Analytics'] } },
        '/v1/webhook-analytics/overview': { get: { summary: 'Webhook overview', tags: ['Webhook Analytics'] } },
        '/v1/webhook-analytics/admin/analytics': { get: { summary: 'Admin analytics', tags: ['Webhook Analytics'] } },
        // Wave 43: Rate Plan Management
        '/v1/rate-plans/plans': { get: { summary: 'List rate plans', tags: ['Rate Plans'] } },
        '/v1/rate-plans/my-plan': { get: { summary: 'My rate plan', tags: ['Rate Plans'] } },
        '/v1/rate-plans/my-limits': { get: { summary: 'Effective limits', tags: ['Rate Plans'] } },
        '/v1/rate-plans/admin/plans': { post: { summary: 'Create plan', tags: ['Rate Plans'] } },
        '/v1/rate-plans/admin/overview': { get: { summary: 'Admin overview', tags: ['Rate Plans'] } },
        // Wave 43: Mission Cost Tracking
        '/v1/mission-costs/costs': { get: { summary: 'Cost breakdown', tags: ['Mission Costs'] } },
        '/v1/mission-costs/costs/by-model': { get: { summary: 'Cost by model', tags: ['Mission Costs'] } },
        '/v1/mission-costs/costs/by-day': { get: { summary: 'Daily costs', tags: ['Mission Costs'] } },
        '/v1/mission-costs/budget': { get: { summary: 'Budget config', tags: ['Mission Costs'] }, put: { summary: 'Set budget', tags: ['Mission Costs'] } },
        '/v1/mission-costs/summary': { get: { summary: 'Cost summary', tags: ['Mission Costs'] } },
        '/v1/mission-costs/admin/overview': { get: { summary: 'Admin cost overview', tags: ['Mission Costs'] } },
        // Wave 44: Tenant Audit Policies
        '/v1/audit-policies/policies': { get: { summary: 'List policies', tags: ['Audit Policies'] }, post: { summary: 'Create policy', tags: ['Audit Policies'] } },
        '/v1/audit-policies/policies/{policyId}': { get: { summary: 'Get policy', tags: ['Audit Policies'] }, put: { summary: 'Update policy', tags: ['Audit Policies'] }, delete: { summary: 'Delete policy', tags: ['Audit Policies'] } },
        '/v1/audit-policies/violations': { get: { summary: 'List violations', tags: ['Audit Policies'] } },
        '/v1/audit-policies/admin/overview': { get: { summary: 'Admin overview', tags: ['Audit Policies'] } },
        // Wave 44: Feature Requests
        '/v1/feature-requests/requests': { get: { summary: 'List requests', tags: ['Feature Requests'] }, post: { summary: 'Submit request', tags: ['Feature Requests'] } },
        '/v1/feature-requests/requests/{requestId}': { get: { summary: 'Get request', tags: ['Feature Requests'] } },
        '/v1/feature-requests/requests/{requestId}/vote': { post: { summary: 'Vote', tags: ['Feature Requests'] }, delete: { summary: 'Remove vote', tags: ['Feature Requests'] } },
        '/v1/feature-requests/requests/{requestId}/comments': { get: { summary: 'List comments', tags: ['Feature Requests'] }, post: { summary: 'Add comment', tags: ['Feature Requests'] } },
        '/v1/feature-requests/admin/overview': { get: { summary: 'Admin overview', tags: ['Feature Requests'] } },
        // Wave 44: Admin Tenant Management
        '/admin/tenant-mgmt/tenants/{tenantId}/notes': { get: { summary: 'List notes', tags: ['Tenant Mgmt'] }, post: { summary: 'Add note', tags: ['Tenant Mgmt'] } },
        '/admin/tenant-mgmt/tenants/{tenantId}/tags': { get: { summary: 'List tags', tags: ['Tenant Mgmt'] }, post: { summary: 'Add tag', tags: ['Tenant Mgmt'] } },
        '/admin/tenant-mgmt/tenants/{tenantId}/risk': { get: { summary: 'Risk score', tags: ['Tenant Mgmt'] } },
        '/admin/tenant-mgmt/at-risk': { get: { summary: 'At-risk tenants', tags: ['Tenant Mgmt'] } },
        '/admin/tenant-mgmt/dashboard': { get: { summary: 'Tenant dashboard', tags: ['Tenant Mgmt'] } },
        // Wave 45
        '/v1/encryption/keys': { get: { summary: 'List encryption keys', tags: ['Encryption'], security: [{ bearer: [] }] }, post: { summary: 'Create key', tags: ['Encryption'], security: [{ bearer: [] }] } },
        '/v1/encryption/keys/{id}/rotate': { post: { summary: 'Rotate key', tags: ['Encryption'], security: [{ bearer: [] }] } },
        '/v1/encryption/keys/{id}/revoke': { post: { summary: 'Revoke key', tags: ['Encryption'], security: [{ bearer: [] }] } },
        '/v1/encryption/audit': { get: { summary: 'Encryption audit trail', tags: ['Encryption'], security: [{ bearer: [] }] } },
        '/v1/encryption/fields': { get: { summary: 'List encrypted fields', tags: ['Encryption'], security: [{ bearer: [] }] }, post: { summary: 'Register field', tags: ['Encryption'], security: [{ bearer: [] }] } },
        '/v1/encryption/stats': { get: { summary: 'Key statistics', tags: ['Encryption'], security: [{ bearer: [] }] } },
        '/v1/encryption/admin/overview': { get: { summary: 'Encryption admin overview', tags: ['Encryption'] } },
        '/v1/mission-debug/missions/{missionId}/steps': { get: { summary: 'Execution steps', tags: ['Mission Debug'], security: [{ bearer: [] }] } },
        '/v1/mission-debug/missions/{missionId}/trace': { get: { summary: 'Full trace', tags: ['Mission Debug'], security: [{ bearer: [] }] } },
        '/v1/mission-debug/sessions': { post: { summary: 'Create debug session', tags: ['Mission Debug'], security: [{ bearer: [] }] } },
        '/v1/mission-debug/sessions/{id}': { get: { summary: 'Get debug session', tags: ['Mission Debug'], security: [{ bearer: [] }] }, put: { summary: 'Update session', tags: ['Mission Debug'], security: [{ bearer: [] }] } },
        '/v1/mission-debug/replay': { post: { summary: 'Start replay', tags: ['Mission Debug'], security: [{ bearer: [] }] } },
        '/v1/mission-debug/replay/{id}': { get: { summary: 'Replay status', tags: ['Mission Debug'], security: [{ bearer: [] }] } },
        '/v1/mission-debug/admin/overview': { get: { summary: 'Debug admin overview', tags: ['Mission Debug'] } },
        '/v1/rate-policies/policies': { get: { summary: 'List rate policies', tags: ['Rate Policies'], security: [{ bearer: [] }] }, post: { summary: 'Create policy', tags: ['Rate Policies'], security: [{ bearer: [] }] } },
        '/v1/rate-policies/policies/{id}': { put: { summary: 'Update policy', tags: ['Rate Policies'], security: [{ bearer: [] }] }, delete: { summary: 'Delete policy', tags: ['Rate Policies'], security: [{ bearer: [] }] } },
        '/v1/rate-policies/templates': { get: { summary: 'List templates', tags: ['Rate Policies'] }, post: { summary: 'Create template', tags: ['Rate Policies'] } },
        '/v1/rate-policies/apply-template': { post: { summary: 'Apply template', tags: ['Rate Policies'], security: [{ bearer: [] }] } },
        '/v1/rate-policies/violations': { get: { summary: 'Get violations', tags: ['Rate Policies'], security: [{ bearer: [] }] } },
        '/v1/rate-policies/stats': { get: { summary: 'Policy stats', tags: ['Rate Policies'], security: [{ bearer: [] }] } },
        '/v1/rate-policies/admin/overview': { get: { summary: 'Rate policies admin', tags: ['Rate Policies'] } },
        // Wave 46
        '/v1/onboarding-checklist': { get: { summary: 'Get checklist', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/init': { post: { summary: 'Initialize checklist', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/steps/{stepKey}/complete': { post: { summary: 'Complete step', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/steps/{stepKey}/claim': { post: { summary: 'Claim reward', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/progress': { get: { summary: 'Get progress', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/milestones': { get: { summary: 'Get milestones', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/milestones/{key}/achieve': { post: { summary: 'Achieve milestone', tags: ['Onboarding Checklist'], security: [{ bearer: [] }] } },
        '/v1/onboarding-checklist/admin/overview': { get: { summary: 'Checklist admin', tags: ['Onboarding Checklist'] } },
        '/v1/i18n/config': { get: { summary: 'Get locale config', tags: ['Localization'], security: [{ bearer: [] }] }, put: { summary: 'Update locale config', tags: ['Localization'], security: [{ bearer: [] }] } },
        '/v1/i18n/translations/{locale}': { get: { summary: 'Get translations', tags: ['Localization'] } },
        '/v1/i18n/translations': { post: { summary: 'Upsert translation', tags: ['Localization'] } },
        '/v1/i18n/keys': { get: { summary: 'List translation keys', tags: ['Localization'] }, post: { summary: 'Create key', tags: ['Localization'] } },
        '/v1/i18n/namespaces/{ns}/{locale}': { get: { summary: 'Namespace translations', tags: ['Localization'] } },
        '/v1/i18n/locales': { get: { summary: 'Supported locales', tags: ['Localization'] } },
        '/v1/i18n/admin/overview': { get: { summary: 'Localization admin', tags: ['Localization'] } },
        '/admin/incidents': { get: { summary: 'List incidents', tags: ['Incidents'] }, post: { summary: 'Create incident', tags: ['Incidents'] } },
        '/admin/incidents/{id}': { get: { summary: 'Get incident', tags: ['Incidents'] }, put: { summary: 'Update incident', tags: ['Incidents'] } },
        '/admin/incidents/{id}/updates': { get: { summary: 'Get updates', tags: ['Incidents'] }, post: { summary: 'Add update', tags: ['Incidents'] } },
        '/admin/incidents/{id}/postmortem': { get: { summary: 'Get postmortem', tags: ['Incidents'] }, post: { summary: 'Create postmortem', tags: ['Incidents'] } },
        '/admin/incidents/active': { get: { summary: 'Active incidents', tags: ['Incidents'] } },
        '/admin/incidents/dashboard': { get: { summary: 'Incident dashboard', tags: ['Incidents'] } },
        // Wave 47
        '/v1/mission-approvals/workflows': { get: { summary: 'List approval workflows', tags: ['Approval Workflow'], security: [{ bearer: [] }] }, post: { summary: 'Create workflow', tags: ['Approval Workflow'], security: [{ bearer: [] }] } },
        '/v1/mission-approvals/workflows/{id}': { get: { summary: 'Get workflow', tags: ['Approval Workflow'], security: [{ bearer: [] }] }, put: { summary: 'Update workflow', tags: ['Approval Workflow'], security: [{ bearer: [] }] } },
        '/v1/mission-approvals/submit': { post: { summary: 'Submit for approval', tags: ['Approval Workflow'], security: [{ bearer: [] }] } },
        '/v1/mission-approvals/requests/{id}': { get: { summary: 'Get approval request', tags: ['Approval Workflow'], security: [{ bearer: [] }] } },
        '/v1/mission-approvals/requests/{id}/decide': { post: { summary: 'Make decision', tags: ['Approval Workflow'], security: [{ bearer: [] }] } },
        '/v1/mission-approvals/pending': { get: { summary: 'Pending approvals', tags: ['Approval Workflow'], security: [{ bearer: [] }] } },
        '/v1/mission-approvals/admin/overview': { get: { summary: 'Approval admin overview', tags: ['Approval Workflow'] } },
        '/v1/security-policies/policies': { get: { summary: 'List security policies', tags: ['Security Policies'], security: [{ bearer: [] }] }, post: { summary: 'Create policy', tags: ['Security Policies'], security: [{ bearer: [] }] } },
        '/v1/security-policies/policies/{id}': { put: { summary: 'Update policy', tags: ['Security Policies'], security: [{ bearer: [] }] }, delete: { summary: 'Delete policy', tags: ['Security Policies'], security: [{ bearer: [] }] } },
        '/v1/security-policies/templates': { get: { summary: 'Policy templates', tags: ['Security Policies'] } },
        '/v1/security-policies/apply-template': { post: { summary: 'Apply template', tags: ['Security Policies'], security: [{ bearer: [] }] } },
        '/v1/security-policies/violations': { get: { summary: 'List violations', tags: ['Security Policies'], security: [{ bearer: [] }] } },
        '/v1/security-policies/violations/{id}/resolve': { post: { summary: 'Resolve violation', tags: ['Security Policies'], security: [{ bearer: [] }] } },
        '/v1/security-policies/compliance': { get: { summary: 'Compliance score', tags: ['Security Policies'], security: [{ bearer: [] }] } },
        '/v1/security-policies/admin/overview': { get: { summary: 'Security admin overview', tags: ['Security Policies'] } },
        '/admin/user-mgmt/users': { get: { summary: 'List admin users', tags: ['Admin Users'] }, post: { summary: 'Create admin user', tags: ['Admin Users'] } },
        '/admin/user-mgmt/users/{id}': { get: { summary: 'Get admin user', tags: ['Admin Users'] }, put: { summary: 'Update admin user', tags: ['Admin Users'] }, delete: { summary: 'Deactivate admin user', tags: ['Admin Users'] } },
        '/admin/user-mgmt/roles': { get: { summary: 'List roles', tags: ['Admin Users'] }, post: { summary: 'Create role', tags: ['Admin Users'] } },
        '/admin/user-mgmt/activity': { get: { summary: 'Activity log', tags: ['Admin Users'] } },
        '/admin/user-mgmt/dashboard': { get: { summary: 'Admin dashboard', tags: ['Admin Users'] } },
        // Wave 48
        '/v1/billing-history/invoices': { get: { summary: 'List invoices', tags: ['Billing History'], security: [{ bearer: [] }] }, post: { summary: 'Create invoice', tags: ['Billing History'], security: [{ bearer: [] }] } },
        '/v1/billing-history/invoices/{id}': { get: { summary: 'Get invoice', tags: ['Billing History'], security: [{ bearer: [] }] } },
        '/v1/billing-history/invoices/{id}/void': { post: { summary: 'Void invoice', tags: ['Billing History'], security: [{ bearer: [] }] } },
        '/v1/billing-history/payments': { get: { summary: 'List payments', tags: ['Billing History'], security: [{ bearer: [] }] }, post: { summary: 'Record payment', tags: ['Billing History'], security: [{ bearer: [] }] } },
        '/v1/billing-history/statements/{month}': { get: { summary: 'Get statement', tags: ['Billing History'], security: [{ bearer: [] }] } },
        '/v1/billing-history/statements/generate': { post: { summary: 'Generate statement', tags: ['Billing History'], security: [{ bearer: [] }] } },
        '/v1/billing-history/admin/overview': { get: { summary: 'Billing admin overview', tags: ['Billing History'] } },
        '/v1/gateway-middleware/configs': { get: { summary: 'List middleware configs', tags: ['Gateway Middleware'], security: [{ bearer: [] }] }, post: { summary: 'Create config', tags: ['Gateway Middleware'], security: [{ bearer: [] }] } },
        '/v1/gateway-middleware/configs/{id}': { put: { summary: 'Update config', tags: ['Gateway Middleware'], security: [{ bearer: [] }] }, delete: { summary: 'Delete config', tags: ['Gateway Middleware'], security: [{ bearer: [] }] } },
        '/v1/gateway-middleware/reorder': { post: { summary: 'Reorder middleware', tags: ['Gateway Middleware'], security: [{ bearer: [] }] } },
        '/v1/gateway-middleware/templates': { get: { summary: 'Middleware templates', tags: ['Gateway Middleware'] } },
        '/v1/gateway-middleware/logs': { get: { summary: 'Execution logs', tags: ['Gateway Middleware'], security: [{ bearer: [] }] } },
        '/v1/gateway-middleware/preview': { get: { summary: 'Preview chain', tags: ['Gateway Middleware'], security: [{ bearer: [] }] } },
        '/v1/gateway-middleware/admin/overview': { get: { summary: 'Middleware admin overview', tags: ['Gateway Middleware'] } },
        '/admin/capacity/snapshots': { get: { summary: 'Get snapshots', tags: ['Capacity Planning'] }, post: { summary: 'Record snapshot', tags: ['Capacity Planning'] } },
        '/admin/capacity/current': { get: { summary: 'Current capacity', tags: ['Capacity Planning'] } },
        '/admin/capacity/forecasts': { get: { summary: 'Get forecasts', tags: ['Capacity Planning'] }, post: { summary: 'Create forecast', tags: ['Capacity Planning'] } },
        '/admin/capacity/recommendations': { get: { summary: 'List recommendations', tags: ['Capacity Planning'] }, post: { summary: 'Create recommendation', tags: ['Capacity Planning'] } },
        '/admin/capacity/recommendations/{id}': { put: { summary: 'Update recommendation', tags: ['Capacity Planning'] } },
        '/admin/capacity/dashboard': { get: { summary: 'Capacity dashboard', tags: ['Capacity Planning'] } },
        // Wave 49
        '/v1/notification-center/notifications': { get: { summary: 'List notifications', tags: ['Notification Center'], security: [{ bearer: [] }] }, post: { summary: 'Create notification', tags: ['Notification Center'], security: [{ bearer: [] }] } },
        '/v1/notification-center/notifications/{id}/read': { put: { summary: 'Mark as read', tags: ['Notification Center'], security: [{ bearer: [] }] } },
        '/v1/notification-center/notifications/read-all': { post: { summary: 'Mark all read', tags: ['Notification Center'], security: [{ bearer: [] }] } },
        '/v1/notification-center/preferences': { get: { summary: 'Get preferences', tags: ['Notification Center'], security: [{ bearer: [] }] } },
        '/v1/notification-center/preferences/{channel}': { put: { summary: 'Update preference', tags: ['Notification Center'], security: [{ bearer: [] }] } },
        '/v1/notification-center/templates': { get: { summary: 'Notification templates', tags: ['Notification Center'] } },
        '/v1/notification-center/admin/overview': { get: { summary: 'Notification admin', tags: ['Notification Center'] } },
        '/v1/mission-templates/templates': { get: { summary: 'List templates', tags: ['Mission Templates'], security: [{ bearer: [] }] }, post: { summary: 'Create template', tags: ['Mission Templates'], security: [{ bearer: [] }] } },
        '/v1/mission-templates/templates/{id}': { get: { summary: 'Get template', tags: ['Mission Templates'], security: [{ bearer: [] }] }, put: { summary: 'Update template', tags: ['Mission Templates'], security: [{ bearer: [] }] }, delete: { summary: 'Delete template', tags: ['Mission Templates'], security: [{ bearer: [] }] } },
        '/v1/mission-templates/categories': { get: { summary: 'List categories', tags: ['Mission Templates'] } },
        '/v1/mission-templates/templates/{id}/instantiate': { post: { summary: 'Instantiate template', tags: ['Mission Templates'], security: [{ bearer: [] }] } },
        '/v1/mission-templates/templates/{id}/versions': { get: { summary: 'Template versions', tags: ['Mission Templates'], security: [{ bearer: [] }] } },
        '/v1/mission-templates/admin/overview': { get: { summary: 'Templates admin', tags: ['Mission Templates'] } },
        '/v1/api-key-mgmt/keys': { get: { summary: 'List API keys', tags: ['API Key Management'], security: [{ bearer: [] }] }, post: { summary: 'Create API key', tags: ['API Key Management'], security: [{ bearer: [] }] } },
        '/v1/api-key-mgmt/keys/{id}': { get: { summary: 'Get key', tags: ['API Key Management'], security: [{ bearer: [] }] }, delete: { summary: 'Revoke key', tags: ['API Key Management'], security: [{ bearer: [] }] } },
        '/v1/api-key-mgmt/keys/{id}/rotate': { post: { summary: 'Rotate key', tags: ['API Key Management'], security: [{ bearer: [] }] } },
        '/v1/api-key-mgmt/keys/{id}/scopes': { put: { summary: 'Update scopes', tags: ['API Key Management'], security: [{ bearer: [] }] } },
        '/v1/api-key-mgmt/keys/{id}/usage': { get: { summary: 'Key usage logs', tags: ['API Key Management'], security: [{ bearer: [] }] } },
        '/v1/api-key-mgmt/admin/overview': { get: { summary: 'API key admin', tags: ['API Key Management'] } },
        // Wave 50
        '/v1/audit-trail/logs': { get: { summary: 'Search audit logs', tags: ['Audit Trail'], security: [{ bearer: [] }] } },
        '/v1/audit-trail/logs/{id}': { get: { summary: 'Log detail', tags: ['Audit Trail'], security: [{ bearer: [] }] } },
        '/v1/audit-trail/retention': { get: { summary: 'Retention policies', tags: ['Audit Trail'], security: [{ bearer: [] }] } },
        '/v1/audit-trail/retention/{resourceType}': { put: { summary: 'Update retention', tags: ['Audit Trail'], security: [{ bearer: [] }] } },
        '/v1/audit-trail/exports': { get: { summary: 'List exports', tags: ['Audit Trail'], security: [{ bearer: [] }] }, post: { summary: 'Request export', tags: ['Audit Trail'], security: [{ bearer: [] }] } },
        '/v1/audit-trail/stats': { get: { summary: 'Audit stats', tags: ['Audit Trail'], security: [{ bearer: [] }] } },
        '/v1/audit-trail/admin/overview': { get: { summary: 'Audit admin', tags: ['Audit Trail'] } },
        '/admin/feature-flags/flags': { get: { summary: 'List flags', tags: ['Feature Flags'] }, post: { summary: 'Create flag', tags: ['Feature Flags'] } },
        '/admin/feature-flags/flags/{id}': { get: { summary: 'Get flag', tags: ['Feature Flags'] }, put: { summary: 'Update flag', tags: ['Feature Flags'] }, delete: { summary: 'Delete flag', tags: ['Feature Flags'] } },
        '/admin/feature-flags/flags/{id}/toggle': { post: { summary: 'Toggle flag', tags: ['Feature Flags'] } },
        '/admin/feature-flags/evaluate/{flagKey}': { get: { summary: 'Evaluate flag', tags: ['Feature Flags'] } },
        '/admin/feature-flags/flags/{id}/overrides': { get: { summary: 'List overrides', tags: ['Feature Flags'] }, post: { summary: 'Set override', tags: ['Feature Flags'] } },
        '/admin/feature-flags/flags/{id}/overrides/{tenantId}': { delete: { summary: 'Remove override', tags: ['Feature Flags'] } },
        '/admin/feature-flags/dashboard': { get: { summary: 'Flags dashboard', tags: ['Feature Flags'] } },
        '/v1/resource-quotas/definitions': { get: { summary: 'Quota definitions', tags: ['Resource Quotas'] }, post: { summary: 'Create definition', tags: ['Resource Quotas'] } },
        '/v1/resource-quotas/definitions/{resourceType}': { put: { summary: 'Update definition', tags: ['Resource Quotas'] } },
        '/v1/resource-quotas/quotas': { get: { summary: 'Tenant quotas', tags: ['Resource Quotas'], security: [{ bearer: [] }] } },
        '/v1/resource-quotas/quotas/{resourceType}': { put: { summary: 'Set quota', tags: ['Resource Quotas'] } },
        '/v1/resource-quotas/check/{resourceType}': { get: { summary: 'Check quota', tags: ['Resource Quotas'], security: [{ bearer: [] }] } },
        '/v1/resource-quotas/usage/{resourceType}': { post: { summary: 'Increment usage', tags: ['Resource Quotas'], security: [{ bearer: [] }] } },
        '/v1/resource-quotas/reset/{resourceType}': { post: { summary: 'Reset usage', tags: ['Resource Quotas'] } },
        '/v1/resource-quotas/alerts': { get: { summary: 'Quota alerts', tags: ['Resource Quotas'], security: [{ bearer: [] }] } },
        '/v1/resource-quotas/alerts/{id}/acknowledge': { post: { summary: 'Acknowledge alert', tags: ['Resource Quotas'], security: [{ bearer: [] }] } },
        '/v1/resource-quotas/admin/overview': { get: { summary: 'Quotas admin', tags: ['Resource Quotas'] } },
        // Wave 51
        '/v1/webhooks-v3/subscriptions': { get: { summary: 'List webhook subscriptions', tags: ['Webhooks V3'], security: [{ bearer: [] }] }, post: { summary: 'Create subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v3/subscriptions/{id}': { get: { summary: 'Get subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] }, put: { summary: 'Update subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] }, delete: { summary: 'Delete subscription', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v3/subscriptions/{id}/test': { post: { summary: 'Test webhook', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v3/subscriptions/{id}/deliveries': { get: { summary: 'Delivery history', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v3/deliveries/{id}/retry': { post: { summary: 'Retry delivery', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v3/event-types': { get: { summary: 'Event types', tags: ['Webhooks V3'] } },
        '/v1/webhooks-v3/stats': { get: { summary: 'Delivery stats', tags: ['Webhooks V3'], security: [{ bearer: [] }] } },
        '/v1/webhooks-v3/admin/overview': { get: { summary: 'Webhooks admin', tags: ['Webhooks V3'] } },
        '/admin/service-mesh/services': { get: { summary: 'List services', tags: ['Service Mesh'] }, post: { summary: 'Register service', tags: ['Service Mesh'] } },
        '/admin/service-mesh/services/{id}': { get: { summary: 'Get service', tags: ['Service Mesh'] }, put: { summary: 'Update service', tags: ['Service Mesh'] }, delete: { summary: 'Deregister', tags: ['Service Mesh'] } },
        '/admin/service-mesh/services/{id}/health': { post: { summary: 'Health check', tags: ['Service Mesh'] } },
        '/admin/service-mesh/services/{id}/circuit-breaker': { get: { summary: 'Get breaker', tags: ['Service Mesh'] }, put: { summary: 'Update breaker', tags: ['Service Mesh'] } },
        '/admin/service-mesh/traffic-rules': { get: { summary: 'Traffic rules', tags: ['Service Mesh'] }, post: { summary: 'Create rule', tags: ['Service Mesh'] } },
        '/admin/service-mesh/topology': { get: { summary: 'Mesh topology', tags: ['Service Mesh'] } },
        '/admin/service-mesh/dashboard': { get: { summary: 'Mesh dashboard', tags: ['Service Mesh'] } },
        '/v1/scheduling/jobs': { get: { summary: 'List scheduled jobs', tags: ['Scheduling'], security: [{ bearer: [] }] }, post: { summary: 'Create job', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/jobs/{id}': { get: { summary: 'Get job', tags: ['Scheduling'], security: [{ bearer: [] }] }, put: { summary: 'Update job', tags: ['Scheduling'], security: [{ bearer: [] }] }, delete: { summary: 'Delete job', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/jobs/{id}/pause': { post: { summary: 'Pause job', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/jobs/{id}/resume': { post: { summary: 'Resume job', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/jobs/{id}/trigger': { post: { summary: 'Trigger job', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/jobs/{id}/executions': { get: { summary: 'Job executions', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/jobs/{id}/skip-rules': { get: { summary: 'Skip rules', tags: ['Scheduling'], security: [{ bearer: [] }] }, post: { summary: 'Add skip rule', tags: ['Scheduling'], security: [{ bearer: [] }] } },
        '/v1/scheduling/admin/overview': { get: { summary: 'Scheduling admin', tags: ['Scheduling'] } },
        // Wave 52
        '/v1/data-export/exports': { get: { summary: 'List exports', tags: ['Data Export'], security: [{ bearer: [] }] }, post: { summary: 'Request export', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/v1/data-export/exports/{id}': { get: { summary: 'Get export', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/v1/data-export/exports/{id}/cancel': { post: { summary: 'Cancel export', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/v1/data-export/exports/{id}/download': { get: { summary: 'Download export', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/v1/data-export/templates': { get: { summary: 'Export templates', tags: ['Data Export'] } },
        '/v1/data-export/templates/{id}/export': { post: { summary: 'Export from template', tags: ['Data Export'], security: [{ bearer: [] }] } },
        '/v1/data-export/admin/overview': { get: { summary: 'Export admin', tags: ['Data Export'] } },
        '/admin/platform-config/configs': { get: { summary: 'List configs', tags: ['Platform Config'] } },
        '/admin/platform-config/configs/{key}': { get: { summary: 'Get config', tags: ['Platform Config'] }, put: { summary: 'Set config', tags: ['Platform Config'] }, delete: { summary: 'Delete config', tags: ['Platform Config'] } },
        '/admin/platform-config/configs/{key}/effective': { get: { summary: 'Effective config', tags: ['Platform Config'] } },
        '/admin/platform-config/configs/{key}/overrides': { get: { summary: 'List overrides', tags: ['Platform Config'] }, post: { summary: 'Set override', tags: ['Platform Config'] } },
        '/admin/platform-config/configs/{key}/history': { get: { summary: 'Config history', tags: ['Platform Config'] } },
        '/admin/platform-config/configs/{key}/rollback': { post: { summary: 'Rollback config', tags: ['Platform Config'] } },
        '/admin/platform-config/dashboard': { get: { summary: 'Config dashboard', tags: ['Platform Config'] } },
        '/admin/contract-testing/contracts': { get: { summary: 'List contracts', tags: ['Contract Testing'] }, post: { summary: 'Create contract', tags: ['Contract Testing'] } },
        '/admin/contract-testing/contracts/{id}': { get: { summary: 'Get contract', tags: ['Contract Testing'] }, put: { summary: 'Update contract', tags: ['Contract Testing'] }, delete: { summary: 'Delete contract', tags: ['Contract Testing'] } },
        '/admin/contract-testing/contracts/{id}/validate': { post: { summary: 'Validate contract', tags: ['Contract Testing'] } },
        '/admin/contract-testing/contracts/{id}/validations': { get: { summary: 'Validations', tags: ['Contract Testing'] } },
        '/admin/contract-testing/breaking-changes': { get: { summary: 'Breaking changes', tags: ['Contract Testing'] } },
        '/admin/contract-testing/breaking-changes/{id}/acknowledge': { post: { summary: 'Acknowledge', tags: ['Contract Testing'] } },
        '/admin/contract-testing/compliance': { get: { summary: 'Compliance report', tags: ['Contract Testing'] } },
        '/admin/contract-testing/dashboard': { get: { summary: 'Testing dashboard', tags: ['Contract Testing'] } },
        // Wave 53
        '/v1/sso-providers/providers': { get: { summary: 'List SSO providers', tags: ['SSO Providers'], security: [{ bearer: [] }] }, post: { summary: 'Create provider', tags: ['SSO Providers'], security: [{ bearer: [] }] } },
        '/v1/sso-providers/providers/{id}': { get: { summary: 'Get provider', tags: ['SSO Providers'], security: [{ bearer: [] }] }, put: { summary: 'Update provider', tags: ['SSO Providers'], security: [{ bearer: [] }] }, delete: { summary: 'Delete provider', tags: ['SSO Providers'], security: [{ bearer: [] }] } },
        '/v1/sso-providers/providers/{id}/login': { post: { summary: 'Initiate login', tags: ['SSO Providers'], security: [{ bearer: [] }] } },
        '/v1/sso-providers/sessions': { get: { summary: 'List sessions', tags: ['SSO Providers'], security: [{ bearer: [] }] } },
        '/v1/sso-providers/sessions/{id}': { delete: { summary: 'Revoke session', tags: ['SSO Providers'], security: [{ bearer: [] }] } },
        '/v1/sso-providers/admin/overview': { get: { summary: 'SSO admin', tags: ['SSO Providers'] } },
        '/v1/priority-queue/enqueue': { post: { summary: 'Enqueue mission', tags: ['Priority Queue'], security: [{ bearer: [] }] } },
        '/v1/priority-queue/dequeue': { post: { summary: 'Dequeue next', tags: ['Priority Queue'] } },
        '/v1/priority-queue/peek': { get: { summary: 'Peek queue', tags: ['Priority Queue'] } },
        '/v1/priority-queue/items/{id}': { get: { summary: 'Get item', tags: ['Priority Queue'], security: [{ bearer: [] }] }, delete: { summary: 'Cancel item', tags: ['Priority Queue'], security: [{ bearer: [] }] } },
        '/v1/priority-queue/items/{id}/priority': { put: { summary: 'Reprioritize', tags: ['Priority Queue'], security: [{ bearer: [] }] } },
        '/v1/priority-queue/rules': { get: { summary: 'List rules', tags: ['Priority Queue'], security: [{ bearer: [] }] }, post: { summary: 'Create rule', tags: ['Priority Queue'], security: [{ bearer: [] }] } },
        '/v1/priority-queue/stats': { get: { summary: 'Queue stats', tags: ['Priority Queue'] } },
        '/v1/priority-queue/admin/overview': { get: { summary: 'Queue admin', tags: ['Priority Queue'] } },
        '/v1/analytics-dashboard/widgets': { get: { summary: 'List widgets', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] }, post: { summary: 'Create widget', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] } },
        '/v1/analytics-dashboard/widgets/{id}': { put: { summary: 'Update widget', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] }, delete: { summary: 'Delete widget', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] } },
        '/v1/analytics-dashboard/queries': { get: { summary: 'List queries', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] }, post: { summary: 'Create query', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] } },
        '/v1/analytics-dashboard/queries/{id}/run': { post: { summary: 'Run query', tags: ['Analytics Dashboard'], security: [{ bearer: [] }] } },
        '/v1/analytics-dashboard/snapshots': { get: { summary: 'Get snapshots', tags: ['Analytics Dashboard'] }, post: { summary: 'Create snapshot', tags: ['Analytics Dashboard'] } },
        '/v1/analytics-dashboard/admin/overview': { get: { summary: 'Dashboard admin', tags: ['Analytics Dashboard'] } },
        // Wave 54
        '/v1/custom-fields/definitions': { get: { summary: 'List field definitions', tags: ['Custom Fields'], security: [{ bearer: [] }] }, post: { summary: 'Create definition', tags: ['Custom Fields'], security: [{ bearer: [] }] } },
        '/v1/custom-fields/definitions/{id}': { get: { summary: 'Get definition', tags: ['Custom Fields'], security: [{ bearer: [] }] }, put: { summary: 'Update definition', tags: ['Custom Fields'], security: [{ bearer: [] }] }, delete: { summary: 'Delete definition', tags: ['Custom Fields'], security: [{ bearer: [] }] } },
        '/v1/custom-fields/values/{entityId}': { get: { summary: 'Get values', tags: ['Custom Fields'], security: [{ bearer: [] }] } },
        '/v1/custom-fields/values/{entityId}/{definitionId}': { put: { summary: 'Set value', tags: ['Custom Fields'], security: [{ bearer: [] }] } },
        '/v1/custom-fields/values/{entityId}/bulk': { post: { summary: 'Bulk set values', tags: ['Custom Fields'], security: [{ bearer: [] }] } },
        '/v1/custom-fields/search': { get: { summary: 'Search by field', tags: ['Custom Fields'], security: [{ bearer: [] }] } },
        '/v1/custom-fields/admin/overview': { get: { summary: 'Fields admin', tags: ['Custom Fields'] } },
        '/admin/deployments/deployments': { get: { summary: 'List deployments', tags: ['Deployments'] }, post: { summary: 'Create deployment', tags: ['Deployments'] } },
        '/admin/deployments/deployments/{id}': { get: { summary: 'Get deployment', tags: ['Deployments'] } },
        '/admin/deployments/deployments/{id}/start': { post: { summary: 'Start deploy', tags: ['Deployments'] } },
        '/admin/deployments/deployments/{id}/rollback': { post: { summary: 'Rollback', tags: ['Deployments'] } },
        '/admin/deployments/deployments/{id}/canary': { get: { summary: 'Canary config', tags: ['Deployments'] }, put: { summary: 'Set canary', tags: ['Deployments'] } },
        '/admin/deployments/dashboard': { get: { summary: 'Deploy dashboard', tags: ['Deployments'] } },
        '/admin/api-docs/endpoints': { get: { summary: 'List endpoints', tags: ['API Docs'] }, post: { summary: 'Create endpoint', tags: ['API Docs'] } },
        '/admin/api-docs/endpoints/{id}': { get: { summary: 'Get endpoint', tags: ['API Docs'] }, put: { summary: 'Update endpoint', tags: ['API Docs'] }, delete: { summary: 'Delete endpoint', tags: ['API Docs'] } },
        '/admin/api-docs/versions': { get: { summary: 'List versions', tags: ['API Docs'] }, post: { summary: 'Create version', tags: ['API Docs'] } },
        '/admin/api-docs/versions/{id}/publish': { post: { summary: 'Publish version', tags: ['API Docs'] } },
        '/admin/api-docs/endpoints/{id}/examples': { get: { summary: 'Get examples', tags: ['API Docs'] }, post: { summary: 'Add example', tags: ['API Docs'] } },
        '/admin/api-docs/dashboard': { get: { summary: 'Docs dashboard', tags: ['API Docs'] } },
        // Wave 55
        '/v1/ip-geo/lookup/{ip}': { get: { summary: 'Lookup IP', tags: ['IP Geolocation'], security: [{ bearer: [] }] } },
        '/v1/ip-geo/rules': { get: { summary: 'List geo rules', tags: ['IP Geolocation'], security: [{ bearer: [] }] }, post: { summary: 'Create rule', tags: ['IP Geolocation'], security: [{ bearer: [] }] } },
        '/v1/ip-geo/rules/{id}': { put: { summary: 'Update rule', tags: ['IP Geolocation'], security: [{ bearer: [] }] }, delete: { summary: 'Delete rule', tags: ['IP Geolocation'], security: [{ bearer: [] }] } },
        '/v1/ip-geo/check': { post: { summary: 'Check access', tags: ['IP Geolocation'], security: [{ bearer: [] }] } },
        '/v1/ip-geo/logs': { get: { summary: 'Access logs', tags: ['IP Geolocation'], security: [{ bearer: [] }] } },
        '/v1/ip-geo/analytics': { get: { summary: 'Geo analytics', tags: ['IP Geolocation'], security: [{ bearer: [] }] } },
        '/v1/ip-geo/admin/overview': { get: { summary: 'Geo admin', tags: ['IP Geolocation'] } },
        '/v1/dep-graph/dependencies': { post: { summary: 'Add dependency', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/dependencies/{id}': { delete: { summary: 'Remove dependency', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/dependencies/{missionId}': { get: { summary: 'Get dependencies', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/graph/{rootMissionId}': { get: { summary: 'Get graph', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/groups': { get: { summary: 'List groups', tags: ['Dependency Graph'], security: [{ bearer: [] }] }, post: { summary: 'Create group', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/analyze/{rootMissionId}': { post: { summary: 'Analyze path', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/analyses': { get: { summary: 'List analyses', tags: ['Dependency Graph'], security: [{ bearer: [] }] } },
        '/v1/dep-graph/admin/overview': { get: { summary: 'Graph admin', tags: ['Dependency Graph'] } },
        '/v1/rate-analytics/events': { get: { summary: 'Rate events', tags: ['Rate Limit Analytics'], security: [{ bearer: [] }] } },
        '/v1/rate-analytics/abuse': { get: { summary: 'Abuse list', tags: ['Rate Limit Analytics'] } },
        '/v1/rate-analytics/history': { get: { summary: 'Throttle history', tags: ['Rate Limit Analytics'], security: [{ bearer: [] }] } },
        '/v1/rate-analytics/stats': { get: { summary: 'Rate stats', tags: ['Rate Limit Analytics'], security: [{ bearer: [] }] } },
        '/v1/rate-analytics/admin/overview': { get: { summary: 'Rate admin', tags: ['Rate Limit Analytics'] } },
        // Wave 56
        '/v1/tags/tags': { get: { summary: 'List tags', tags: ['Tag System'], security: [{ bearer: [] }] }, post: { summary: 'Create tag', tags: ['Tag System'], security: [{ bearer: [] }] } },
        '/v1/tags/tags/{id}': { put: { summary: 'Update tag', tags: ['Tag System'], security: [{ bearer: [] }] }, delete: { summary: 'Delete tag', tags: ['Tag System'], security: [{ bearer: [] }] } },
        '/v1/tags/entities/{entityType}/{entityId}/tags': { get: { summary: 'Entity tags', tags: ['Tag System'], security: [{ bearer: [] }] } },
        '/v1/tags/entities/{entityType}/{entityId}/tags/{tagId}': { post: { summary: 'Tag entity', tags: ['Tag System'], security: [{ bearer: [] }] }, delete: { summary: 'Untag entity', tags: ['Tag System'], security: [{ bearer: [] }] } },
        '/v1/tags/tags/{id}/entities': { get: { summary: 'Find by tag', tags: ['Tag System'], security: [{ bearer: [] }] } },
        '/v1/tags/analytics': { get: { summary: 'Tag analytics', tags: ['Tag System'], security: [{ bearer: [] }] } },
        '/v1/tags/admin/overview': { get: { summary: 'Tags admin', tags: ['Tag System'] } },
        '/admin/system-health/metrics/{name}': { get: { summary: 'Get metrics', tags: ['System Health'] } },
        '/admin/system-health/components': { get: { summary: 'List components', tags: ['System Health'] }, put: { summary: 'Update component', tags: ['System Health'] } },
        '/admin/system-health/uptime/{component}': { get: { summary: 'Uptime history', tags: ['System Health'] } },
        '/admin/system-health/alerts': { get: { summary: 'Alert rules', tags: ['System Health'] }, post: { summary: 'Create alert', tags: ['System Health'] } },
        '/admin/system-health/alerts/{id}': { put: { summary: 'Update alert', tags: ['System Health'] }, delete: { summary: 'Delete alert', tags: ['System Health'] } },
        '/admin/system-health/check-alerts': { post: { summary: 'Check alerts', tags: ['System Health'] } },
        '/admin/system-health/dashboard': { get: { summary: 'Health dashboard', tags: ['System Health'] } },
        '/admin/response-cache/rules': { get: { summary: 'Cache rules', tags: ['Response Cache'] }, post: { summary: 'Create rule', tags: ['Response Cache'] } },
        '/admin/response-cache/rules/{id}': { put: { summary: 'Update rule', tags: ['Response Cache'] }, delete: { summary: 'Delete rule', tags: ['Response Cache'] } },
        '/admin/response-cache/entries/{cacheKey}': { get: { summary: 'Get entry', tags: ['Response Cache'] } },
        '/admin/response-cache/invalidate/path': { post: { summary: 'Invalidate path', tags: ['Response Cache'] } },
        '/admin/response-cache/purge': { post: { summary: 'Purge expired', tags: ['Response Cache'] } },
        '/admin/response-cache/analytics': { get: { summary: 'Cache analytics', tags: ['Response Cache'] } },
        '/admin/response-cache/dashboard': { get: { summary: 'Cache dashboard', tags: ['Response Cache'] } },
        // Wave 57
        '/v1/workspace/settings': { get: { summary: 'Get workspace settings', tags: ['Workspace'], security: [{ bearer: [] }] }, put: { summary: 'Update settings', tags: ['Workspace'], security: [{ bearer: [] }] } },
        '/v1/workspace/settings/reset': { post: { summary: 'Reset settings', tags: ['Workspace'], security: [{ bearer: [] }] } },
        '/v1/workspace/invitations': { get: { summary: 'List invitations', tags: ['Workspace'], security: [{ bearer: [] }] }, post: { summary: 'Create invitation', tags: ['Workspace'], security: [{ bearer: [] }] } },
        '/v1/workspace/invitations/{id}': { delete: { summary: 'Cancel invitation', tags: ['Workspace'], security: [{ bearer: [] }] } },
        '/v1/workspace/invitations/{id}/accept': { post: { summary: 'Accept invitation', tags: ['Workspace'] } },
        '/v1/workspace/admin/overview': { get: { summary: 'Workspace admin', tags: ['Workspace'] } },
        '/v1/results/results': { post: { summary: 'Store result', tags: ['Result Storage'], security: [{ bearer: [] }] } },
        '/v1/results/results/{missionId}': { get: { summary: 'Get result', tags: ['Result Storage'], security: [{ bearer: [] }] } },
        '/v1/results/results/{missionId}/versions': { get: { summary: 'Result versions', tags: ['Result Storage'], security: [{ bearer: [] }] } },
        '/v1/results/results/{resultId}/attachments': { get: { summary: 'List attachments', tags: ['Result Storage'], security: [{ bearer: [] }] }, post: { summary: 'Add attachment', tags: ['Result Storage'], security: [{ bearer: [] }] } },
        '/v1/results/stats': { get: { summary: 'Storage stats', tags: ['Result Storage'], security: [{ bearer: [] }] } },
        '/v1/results/admin/overview': { get: { summary: 'Results admin', tags: ['Result Storage'] } },
        '/admin/event-log/events': { get: { summary: 'List events', tags: ['Event Log'] }, post: { summary: 'Log event', tags: ['Event Log'] } },
        '/admin/event-log/events/{id}': { get: { summary: 'Get event', tags: ['Event Log'] } },
        '/admin/event-log/categories': { get: { summary: 'List categories', tags: ['Event Log'] }, post: { summary: 'Create category', tags: ['Event Log'] } },
        '/admin/event-log/retention': { get: { summary: 'Retention configs', tags: ['Event Log'] } },
        '/admin/event-log/retention/{category}': { put: { summary: 'Update retention', tags: ['Event Log'] } },
        '/admin/event-log/stats': { get: { summary: 'Event stats', tags: ['Event Log'] } },
        '/admin/event-log/dashboard': { get: { summary: 'Event dashboard', tags: ['Event Log'] } },
        // Wave 58
        '/v1/access-tokens/tokens': { get: { summary: 'List tokens', tags: ['Access Tokens'], security: [{ bearer: [] }] }, post: { summary: 'Create token', tags: ['Access Tokens'], security: [{ bearer: [] }] } },
        '/v1/access-tokens/tokens/{id}': { delete: { summary: 'Revoke token', tags: ['Access Tokens'], security: [{ bearer: [] }] } },
        '/v1/access-tokens/tokens/{id}/usage': { get: { summary: 'Token usage', tags: ['Access Tokens'], security: [{ bearer: [] }] } },
        '/v1/access-tokens/introspect': { post: { summary: 'Introspect token', tags: ['Access Tokens'] } },
        '/v1/access-tokens/refresh': { post: { summary: 'Refresh token', tags: ['Access Tokens'] } },
        '/v1/access-tokens/revoke-all': { post: { summary: 'Revoke all', tags: ['Access Tokens'], security: [{ bearer: [] }] } },
        '/v1/access-tokens/admin/overview': { get: { summary: 'Tokens admin', tags: ['Access Tokens'] } },
        '/admin/tenant-analytics/health': { get: { summary: 'Health scores', tags: ['Tenant Analytics'] } },
        '/admin/tenant-analytics/health/{tenantId}': { get: { summary: 'Tenant health', tags: ['Tenant Analytics'] } },
        '/admin/tenant-analytics/health/{tenantId}/calculate': { post: { summary: 'Calculate health', tags: ['Tenant Analytics'] } },
        '/admin/tenant-analytics/trends/{tenantId}': { get: { summary: 'Usage trends', tags: ['Tenant Analytics'] } },
        '/admin/tenant-analytics/risks': { get: { summary: 'Risk indicators', tags: ['Tenant Analytics'] } },
        '/admin/tenant-analytics/report/{tenantId}': { get: { summary: 'Tenant report', tags: ['Tenant Analytics'] } },
        '/admin/tenant-analytics/dashboard': { get: { summary: 'Analytics dashboard', tags: ['Tenant Analytics'] } },
        '/admin/endpoint-monitoring/metrics/{path}': { get: { summary: 'Endpoint metrics', tags: ['Endpoint Monitoring'] } },
        '/admin/endpoint-monitoring/stats/{path}': { get: { summary: 'Endpoint stats', tags: ['Endpoint Monitoring'] } },
        '/admin/endpoint-monitoring/availability': { get: { summary: 'Availability list', tags: ['Endpoint Monitoring'] } },
        '/admin/endpoint-monitoring/alerts': { get: { summary: 'Monitoring alerts', tags: ['Endpoint Monitoring'] }, post: { summary: 'Create alert', tags: ['Endpoint Monitoring'] } },
        '/admin/endpoint-monitoring/alerts/{id}': { put: { summary: 'Update alert', tags: ['Endpoint Monitoring'] }, delete: { summary: 'Delete alert', tags: ['Endpoint Monitoring'] } },
        '/admin/endpoint-monitoring/slow': { get: { summary: 'Slow endpoints', tags: ['Endpoint Monitoring'] } },
        '/admin/endpoint-monitoring/dashboard': { get: { summary: 'Monitoring dashboard', tags: ['Endpoint Monitoring'] } },
        // Wave 59
        '/v1/data-retention/runs': { get: { summary: 'List retention runs', tags: ['Data Retention'] } },
        '/v1/execution-history/executions': { get: { summary: 'List execution history', tags: ['Execution History'] }, post: { summary: 'Record execution', tags: ['Execution History'] } },
        '/v1/execution-history/metrics': { get: { summary: 'Execution metrics', tags: ['Execution History'] } },
        '/admin/error-budget/budgets': { get: { summary: 'List error budgets', tags: ['Error Budget'] }, post: { summary: 'Create error budget', tags: ['Error Budget'] } },
        '/admin/error-budget/events': { get: { summary: 'Budget events', tags: ['Error Budget'] } },
        '/admin/error-budget/dashboard': { get: { summary: 'Error budget dashboard', tags: ['Error Budget'] } },
        // Wave 60
        '/v1/api-versioning/versions': { get: { summary: 'List API versions', tags: ['API Versioning'] }, post: { summary: 'Create API version', tags: ['API Versioning'] } },
        '/v1/api-versioning/mappings': { get: { summary: 'List version mappings', tags: ['API Versioning'] } },
        '/admin/capacity-planning/plans': { get: { summary: 'List capacity plans', tags: ['Capacity Planning'] }, post: { summary: 'Create capacity plan', tags: ['Capacity Planning'] } },
        '/admin/capacity-planning/alerts': { get: { summary: 'Capacity alerts', tags: ['Capacity Planning'] } },
        '/admin/capacity-planning/dashboard': { get: { summary: 'Capacity dashboard', tags: ['Capacity Planning'] } },
        '/v1/compliance-reports/reports': { get: { summary: 'List compliance reports', tags: ['Compliance Reports'] }, post: { summary: 'Create compliance report', tags: ['Compliance Reports'] } },
        '/v1/compliance-reports/rules': { get: { summary: 'List compliance rules', tags: ['Compliance Reports'] } },
        // Wave 61
        '/v1/notification-channels/channels': { get: { summary: 'List notification channels', tags: ['Notification Channels'] }, post: { summary: 'Create channel', tags: ['Notification Channels'] } },
        '/v1/notification-channels/deliveries': { get: { summary: 'List deliveries', tags: ['Notification Channels'] } },
        '/admin/audit-policies/policies': { get: { summary: 'List audit policies', tags: ['Audit Policies'] }, post: { summary: 'Create audit policy', tags: ['Audit Policies'] } },
        '/admin/audit-policies/violations': { get: { summary: 'List violations', tags: ['Audit Policies'] } },
        '/admin/audit-policies/dashboard': { get: { summary: 'Audit dashboard', tags: ['Audit Policies'] } },
        // Wave 62
        '/v1/encryption-keys/keys': { get: { summary: 'List encryption keys', tags: ['Encryption Keys'] }, post: { summary: 'Create key', tags: ['Encryption Keys'] } },
        '/v1/encryption-keys/usage': { get: { summary: 'Key usage logs', tags: ['Encryption Keys'] } },
        '/admin/traffic-shaping/rules': { get: { summary: 'List traffic rules', tags: ['Traffic Shaping'] }, post: { summary: 'Create traffic rule', tags: ['Traffic Shaping'] } },
        '/admin/traffic-shaping/events': { get: { summary: 'Traffic events', tags: ['Traffic Shaping'] } },
        '/admin/traffic-shaping/dashboard': { get: { summary: 'Traffic dashboard', tags: ['Traffic Shaping'] } },
        '/v1/integrations/integrations': { get: { summary: 'List integrations', tags: ['Integrations'] }, post: { summary: 'Create integration', tags: ['Integrations'] } },
        '/v1/integrations/logs': { get: { summary: 'Integration logs', tags: ['Integrations'] } },
        // Wave 63
        '/v1/retry-policies/policies': { get: { summary: 'List retry policies', tags: ['Retry Policies'] }, post: { summary: 'Create retry policy', tags: ['Retry Policies'] } },
        '/v1/retry-policies/attempts': { get: { summary: 'List retry attempts', tags: ['Retry Policies'] } },
        '/admin/feature-usage/usage': { get: { summary: 'Feature usage stats', tags: ['Feature Usage'] }, post: { summary: 'Record usage', tags: ['Feature Usage'] } },
        '/admin/feature-usage/adoption': { get: { summary: 'Feature adoption', tags: ['Feature Usage'] } },
        '/admin/feature-usage/dashboard': { get: { summary: 'Usage dashboard', tags: ['Feature Usage'] } },
        // Wave 64
        '/v1/api-throttling/rules': { get: { summary: 'List throttle rules', tags: ['API Throttling'] }, post: { summary: 'Create throttle rule', tags: ['API Throttling'] } },
        '/v1/api-throttling/events': { get: { summary: 'Throttle events', tags: ['API Throttling'] } },
        '/admin/incident-response/incidents': { get: { summary: 'List incidents', tags: ['Incident Response'] }, post: { summary: 'Create incident', tags: ['Incident Response'] } },
        '/admin/incident-response/updates': { get: { summary: 'Incident updates', tags: ['Incident Response'] } },
        '/admin/incident-response/dashboard': { get: { summary: 'Incident dashboard', tags: ['Incident Response'] } },
        '/v1/export-schedules/schedules': { get: { summary: 'List export schedules', tags: ['Export Schedules'] }, post: { summary: 'Create schedule', tags: ['Export Schedules'] } },
        '/v1/export-schedules/runs': { get: { summary: 'Export runs', tags: ['Export Schedules'] } },
        // Wave 65
        '/v1/sessions/sessions': { get: { summary: 'List sessions', tags: ['Sessions'] }, post: { summary: 'Create session', tags: ['Sessions'] } },
        '/v1/sessions/events': { get: { summary: 'Session events', tags: ['Sessions'] } },
        '/v1/quality-gates/gates': { get: { summary: 'List quality gates', tags: ['Quality Gates'] }, post: { summary: 'Create gate', tags: ['Quality Gates'] } },
        '/v1/quality-gates/evaluations': { get: { summary: 'Gate evaluations', tags: ['Quality Gates'] } },
        '/admin/resource-pools/pools': { get: { summary: 'List resource pools', tags: ['Resource Pools'] }, post: { summary: 'Create pool', tags: ['Resource Pools'] } },
        '/admin/resource-pools/allocations': { get: { summary: 'Pool allocations', tags: ['Resource Pools'] } },
        '/admin/resource-pools/dashboard': { get: { summary: 'Resource dashboard', tags: ['Resource Pools'] } },
        // Wave 66
        '/v1/api-docs-tenant/pages': { get: { summary: 'List doc pages', tags: ['API Docs'] }, post: { summary: 'Create doc page', tags: ['API Docs'] } },
        '/v1/api-docs-tenant/versions': { get: { summary: 'Doc versions', tags: ['API Docs'] } },
        '/admin/change-management/changes': { get: { summary: 'List changes', tags: ['Change Management'] }, post: { summary: 'Create change', tags: ['Change Management'] } },
        '/admin/change-management/logs': { get: { summary: 'Change logs', tags: ['Change Management'] } },
        '/admin/change-management/dashboard': { get: { summary: 'Change dashboard', tags: ['Change Management'] } },
        '/v1/usage-alerts/triggers': { get: { summary: 'Alert triggers', tags: ['Usage Alerts'] } },
        '/v1/api-rate-quotas/quotas': { get: { summary: 'List rate quotas', tags: ['API Rate Quotas'] }, post: { summary: 'Create rate quota', tags: ['API Rate Quotas'] } },
        '/v1/api-rate-quotas/usage': { get: { summary: 'Quota usage stats', tags: ['API Rate Quotas'] } },
        '/v1/execution-metrics/metrics': { get: { summary: 'List execution metrics', tags: ['Execution Metrics'] }, post: { summary: 'Record metric', tags: ['Execution Metrics'] } },
        '/v1/execution-metrics/aggregates': { get: { summary: 'Execution aggregates', tags: ['Execution Metrics'] } },
        '/admin/service-registry/services': { get: { summary: 'List services', tags: ['Service Registry'] }, post: { summary: 'Register service', tags: ['Service Registry'] } },
        '/admin/service-registry/health-checks': { get: { summary: 'Service health checks', tags: ['Service Registry'] } },
        '/v1/data-masking/policies': { get: { summary: 'List masking policies', tags: ['Data Masking'] }, post: { summary: 'Create masking policy', tags: ['Data Masking'] } },
        '/v1/data-masking/events': { get: { summary: 'Masking events', tags: ['Data Masking'] } },
        '/admin/deployment-tracking/deployments': { get: { summary: 'List deployments', tags: ['Deployment Tracking'] }, post: { summary: 'Create deployment', tags: ['Deployment Tracking'] } },
        '/admin/deployment-tracking/rollbacks': { get: { summary: 'Deployment rollbacks', tags: ['Deployment Tracking'] } },
        '/v1/gateway-logs/logs': { get: { summary: 'List gateway logs', tags: ['Gateway Logs'] }, post: { summary: 'Record log', tags: ['Gateway Logs'] } },
        '/v1/gateway-logs/filters': { get: { summary: 'Log filters', tags: ['Gateway Logs'] } },
        '/v1/response-transform/transforms': { get: { summary: 'List response transforms', tags: ['Response Transform'] }, post: { summary: 'Create transform', tags: ['Response Transform'] } },
        '/v1/response-transform/logs': { get: { summary: 'Transform logs', tags: ['Response Transform'] } },
        '/v1/sla-compliance/policies': { get: { summary: 'List SLA policies', tags: ['SLA Compliance'] }, post: { summary: 'Create SLA policy', tags: ['SLA Compliance'] } },
        '/v1/sla-compliance/violations': { get: { summary: 'SLA violations', tags: ['SLA Compliance'] } },
        '/admin/license-management/licenses': { get: { summary: 'List licenses', tags: ['License Management'] }, post: { summary: 'Create license', tags: ['License Management'] } },
        '/admin/license-management/activations': { get: { summary: 'License activations', tags: ['License Management'] } },
        '/v1/data-pipeline/pipelines': { get: { summary: 'List pipelines', tags: ['Data Pipeline'] }, post: { summary: 'Create pipeline', tags: ['Data Pipeline'] } },
        '/v1/data-pipeline/runs': { get: { summary: 'Pipeline runs', tags: ['Data Pipeline'] } },
        '/admin/platform-backup/backups': { get: { summary: 'List backups', tags: ['Platform Backup'] }, post: { summary: 'Create backup', tags: ['Platform Backup'] } },
        '/admin/platform-backup/restore-points': { get: { summary: 'Restore points', tags: ['Platform Backup'] } },
        '/v1/api-mocks/mocks': { get: { summary: 'List mock endpoints', tags: ['API Mock Server'] }, post: { summary: 'Create mock', tags: ['API Mock Server'] } },
        '/v1/api-mocks/requests': { get: { summary: 'Mock requests log', tags: ['API Mock Server'] } },
        '/v1/webhook-templates/templates': { get: { summary: 'List webhook templates', tags: ['Webhook Templates'] }, post: { summary: 'Create template', tags: ['Webhook Templates'] } },
        '/v1/webhook-templates/usage': { get: { summary: 'Template usage', tags: ['Webhook Templates'] } },
        '/v1/cost-optimization/rules': { get: { summary: 'List optimization rules', tags: ['Cost Optimization'] }, post: { summary: 'Create rule', tags: ['Cost Optimization'] } },
        '/v1/cost-optimization/events': { get: { summary: 'Optimization events', tags: ['Cost Optimization'] } },
        '/admin/tenant-grouping/groups': { get: { summary: 'List tenant groups', tags: ['Tenant Grouping'] }, post: { summary: 'Create group', tags: ['Tenant Grouping'] } },
        '/admin/tenant-grouping/members': { get: { summary: 'Group members', tags: ['Tenant Grouping'] } },
        '/v1/schema-validation/rules': { get: { summary: 'List schema rules', tags: ['Schema Validation'] }, post: { summary: 'Create schema rule', tags: ['Schema Validation'] } },
        '/v1/schema-validation/violations': { get: { summary: 'Schema violations', tags: ['Schema Validation'] } },
        '/admin/platform-alerts/rules': { get: { summary: 'List alert rules', tags: ['Platform Alerts'] }, post: { summary: 'Create alert rule', tags: ['Platform Alerts'] } },
        '/admin/platform-alerts/incidents': { get: { summary: 'Alert incidents', tags: ['Platform Alerts'] } },
        '/v1/workflow-automation/workflows': { get: { summary: 'List workflows', tags: ['Workflow Automation'] }, post: { summary: 'Create workflow', tags: ['Workflow Automation'] } },
        '/v1/workflow-automation/runs': { get: { summary: 'Workflow runs', tags: ['Workflow Automation'] } },
        '/v1/api-changelog/entries': { get: { summary: 'List changelog entries', tags: ['API Changelog'] }, post: { summary: 'Create entry', tags: ['API Changelog'] } },
        '/v1/api-changelog/subscriptions': { get: { summary: 'Changelog subscriptions', tags: ['API Changelog'] } },
        '/v1/queue-priority/queues': { get: { summary: 'List priority queues', tags: ['Queue Priority'] }, post: { summary: 'Create queue', tags: ['Queue Priority'] } },
        '/v1/queue-priority/items': { get: { summary: 'Queue items', tags: ['Queue Priority'] } },
        '/admin/compliance-audit/checks': { get: { summary: 'List compliance checks', tags: ['Compliance Audit'] }, post: { summary: 'Create check', tags: ['Compliance Audit'] } },
        '/admin/compliance-audit/results': { get: { summary: 'Compliance results', tags: ['Compliance Audit'] } },
        '/v1/secret-vault/secrets': { get: { summary: 'List secrets', tags: ['Secret Vault'] }, post: { summary: 'Create secret', tags: ['Secret Vault'] } },
        '/v1/secret-vault/access-logs': { get: { summary: 'Secret access logs', tags: ['Secret Vault'] } },
        '/admin/platform-migration/migrations': { get: { summary: 'List migrations', tags: ['Platform Migration'] }, post: { summary: 'Create migration', tags: ['Platform Migration'] } },
        '/admin/platform-migration/rollbacks': { get: { summary: 'Migration rollbacks', tags: ['Platform Migration'] } },
        '/v1/event-replay/configs': { get: { summary: 'List replay configs', tags: ['Event Replay'] }, post: { summary: 'Create config', tags: ['Event Replay'] } },
        '/v1/event-replay/runs': { get: { summary: 'Replay runs', tags: ['Event Replay'] } },
        '/v1/api-deprecation/notices': { get: { summary: 'List deprecation notices', tags: ['API Deprecation'] }, post: { summary: 'Create notice', tags: ['API Deprecation'] } },
        '/v1/api-deprecation/acknowledgements': { get: { summary: 'Deprecation acknowledgements', tags: ['API Deprecation'] } },
        '/v1/artifact-storage/artifacts': { get: { summary: 'List artifacts', tags: ['Artifact Storage'] }, post: { summary: 'Create artifact', tags: ['Artifact Storage'] } },
        '/v1/artifact-storage/downloads': { get: { summary: 'Artifact downloads', tags: ['Artifact Storage'] } },
        '/admin/tenant-scoring/scores': { get: { summary: 'List tenant scores', tags: ['Tenant Scoring'] }, post: { summary: 'Calculate score', tags: ['Tenant Scoring'] } },
        '/admin/tenant-scoring/history': { get: { summary: 'Score history', tags: ['Tenant Scoring'] } },
        '/v1/custom-metrics/metrics': { get: { summary: 'List custom metrics', tags: ['Custom Metrics'] }, post: { summary: 'Create metric', tags: ['Custom Metrics'] } },
        '/v1/custom-metrics/data-points': { get: { summary: 'Metric data points', tags: ['Custom Metrics'] } },
        '/admin/platform-scaling/rules': { get: { summary: 'List scaling rules', tags: ['Platform Scaling'] }, post: { summary: 'Create rule', tags: ['Platform Scaling'] } },
        '/admin/platform-scaling/events': { get: { summary: 'Scaling events', tags: ['Platform Scaling'] } },
        '/v1/notification-digest/configs': { get: { summary: 'List digest configs', tags: ['Notification Digest'] }, post: { summary: 'Create config', tags: ['Notification Digest'] } },
        '/v1/notification-digest/deliveries': { get: { summary: 'Digest deliveries', tags: ['Notification Digest'] } },
        '/v1/access-control/rules': { get: { summary: 'List access rules', tags: ['Access Control'] }, post: { summary: 'Create access rule', tags: ['Access Control'] } },
        '/v1/access-control/audit': { get: { summary: 'Access audit log', tags: ['Access Control'] } },
        '/v1/feedback-loop/feedback': { get: { summary: 'List feedback', tags: ['Feedback Loop'] }, post: { summary: 'Submit feedback', tags: ['Feedback Loop'] } },
        '/v1/feedback-loop/actions': { get: { summary: 'Feedback actions', tags: ['Feedback Loop'] } },
        '/admin/cost-dashboard/entries': { get: { summary: 'List cost entries', tags: ['Cost Dashboard'] }, post: { summary: 'Create cost entry', tags: ['Cost Dashboard'] } },
        '/admin/cost-dashboard/budgets': { get: { summary: 'Cost budgets', tags: ['Cost Dashboard'] } },
        '/v1/data-classification/classifications': { get: { summary: 'List classifications', tags: ['Data Classification'] }, post: { summary: 'Create classification', tags: ['Data Classification'] } },
        '/v1/data-classification/scans': { get: { summary: 'Classification scans', tags: ['Data Classification'] } },
        '/admin/tenant-communication/messages': { get: { summary: 'List messages', tags: ['Tenant Communication'] }, post: { summary: 'Send message', tags: ['Tenant Communication'] } },
        '/admin/tenant-communication/templates': { get: { summary: 'Message templates', tags: ['Tenant Communication'] } },
        '/v1/integration-testing/configs': { get: { summary: 'List test configs', tags: ['Integration Testing'] }, post: { summary: 'Create test config', tags: ['Integration Testing'] } },
        '/v1/integration-testing/results': { get: { summary: 'Test results', tags: ['Integration Testing'] } },
        '/v1/playground-configs/configs': { get: { summary: 'List playground configs', tags: ['Playground Configs'] }, post: { summary: 'Create config', tags: ['Playground Configs'] } },
        '/v1/playground-configs/executions': { get: { summary: 'Playground executions', tags: ['Playground Configs'] } },
        '/v1/chain-orchestration/chains': { get: { summary: 'List mission chains', tags: ['Chain Orchestration'] }, post: { summary: 'Create chain', tags: ['Chain Orchestration'] } },
        '/v1/chain-orchestration/runs': { get: { summary: 'Chain runs', tags: ['Chain Orchestration'] } },
        '/admin/feature-gating/gates': { get: { summary: 'List feature gates', tags: ['Feature Gating'] }, post: { summary: 'Create gate', tags: ['Feature Gating'] } },
        '/admin/feature-gating/overrides': { get: { summary: 'Gate overrides', tags: ['Feature Gating'] } },
        '/v1/consent-management/records': { get: { summary: 'List consent records', tags: ['Consent Management'] }, post: { summary: 'Record consent', tags: ['Consent Management'] } },
        '/v1/consent-management/policies': { get: { summary: 'Consent policies', tags: ['Consent Management'] } },
        '/admin/platform-diagnostics/checks': { get: { summary: 'List diagnostic checks', tags: ['Platform Diagnostics'] }, post: { summary: 'Run check', tags: ['Platform Diagnostics'] } },
        '/admin/platform-diagnostics/reports': { get: { summary: 'Diagnostic reports', tags: ['Platform Diagnostics'] } },
        '/v1/rate-burst/configs': { get: { summary: 'List burst configs', tags: ['Rate Burst'] }, post: { summary: 'Create config', tags: ['Rate Burst'] } },
        '/v1/rate-burst/events': { get: { summary: 'Burst events', tags: ['Rate Burst'] } },
        '/v1/key-rotation/rotations': { get: { summary: 'List key rotations', tags: ['Key Rotation'] }, post: { summary: 'Create rotation', tags: ['Key Rotation'] } },
        '/v1/key-rotation/history': { get: { summary: 'Rotation history', tags: ['Key Rotation'] } },
        '/v1/dependency-graph/dependencies': { get: { summary: 'List dependencies', tags: ['Dependency Graph'] }, post: { summary: 'Create dependency', tags: ['Dependency Graph'] } },
        '/v1/dependency-graph/runs': { get: { summary: 'Dependency runs', tags: ['Dependency Graph'] } },
        '/admin/platform-changelog/entries': { get: { summary: 'List changelog entries', tags: ['Platform Changelog'] }, post: { summary: 'Create entry', tags: ['Platform Changelog'] } },
        '/admin/platform-changelog/subscribers': { get: { summary: 'List subscribers', tags: ['Platform Changelog'] } },
        '/admin/incident-management/incidents': { get: { summary: 'List incidents', tags: ['Incident Management'] }, post: { summary: 'Create incident', tags: ['Incident Management'] } },
        '/admin/incident-management/updates': { get: { summary: 'Incident updates', tags: ['Incident Management'] } },
        '/v1/api-sandbox/sandboxes': { get: { summary: 'List sandboxes', tags: ['API Sandbox'] }, post: { summary: 'Create sandbox', tags: ['API Sandbox'] } },
        '/v1/api-sandbox/requests': { get: { summary: 'Sandbox requests', tags: ['API Sandbox'] } },
        '/v1/webhook-signatures/keys': { get: { summary: 'List signing keys', tags: ['Webhook Signatures'] }, post: { summary: 'Create key', tags: ['Webhook Signatures'] } },
        '/v1/webhook-signatures/logs': { get: { summary: 'Signature logs', tags: ['Webhook Signatures'] } },
        '/v1/cost-tracking/costs': { get: { summary: 'List costs', tags: ['Cost Tracking'] }, post: { summary: 'Record cost', tags: ['Cost Tracking'] } },
        '/v1/cost-tracking/budgets': { get: { summary: 'Cost budgets', tags: ['Cost Tracking'] } },
        '/admin/platform-maintenance/windows': { get: { summary: 'List windows', tags: ['Platform Maintenance'] }, post: { summary: 'Create window', tags: ['Platform Maintenance'] } },
        '/admin/platform-maintenance/notifications': { get: { summary: 'Maintenance notifications', tags: ['Platform Maintenance'] } },
        '/v1/usage-analytics/analytics': { get: { summary: 'List analytics', tags: ['Usage Analytics'] }, post: { summary: 'Record analytic', tags: ['Usage Analytics'] } },
        '/v1/usage-analytics/summaries': { get: { summary: 'Usage summaries', tags: ['Usage Analytics'] } },
        '/admin/tenant-migration/migrations': { get: { summary: 'List migrations', tags: ['Tenant Migration'] }, post: { summary: 'Create migration', tags: ['Tenant Migration'] } },
        '/admin/tenant-migration/steps': { get: { summary: 'Migration steps', tags: ['Tenant Migration'] } },
        '/v1/notification-preferences/preferences': { get: { summary: 'List preferences', tags: ['Notification Preferences'] }, post: { summary: 'Create preference', tags: ['Notification Preferences'] } },
        '/v1/notification-preferences/channels': { get: { summary: 'Notification channels', tags: ['Notification Preferences'] } },
        '/v1/versioning-config/configs': { get: { summary: 'List versioning configs', tags: ['Versioning Config'] }, post: { summary: 'Create config', tags: ['Versioning Config'] } },
        '/v1/versioning-config/mappings': { get: { summary: 'Version mappings', tags: ['Versioning Config'] } },
        '/v1/quality-scoring/scores': { get: { summary: 'List quality scores', tags: ['Quality Scoring'] }, post: { summary: 'Create score', tags: ['Quality Scoring'] } },
        '/v1/quality-scoring/criteria': { get: { summary: 'Scoring criteria', tags: ['Quality Scoring'] } },
        '/admin/platform-compliance/requirements': { get: { summary: 'List requirements', tags: ['Platform Compliance'] }, post: { summary: 'Create requirement', tags: ['Platform Compliance'] } },
        '/admin/platform-compliance/audits': { get: { summary: 'Compliance audits', tags: ['Platform Compliance'] } },
        '/v1/data-retention/executions': { get: { summary: 'Retention executions', tags: ['Data Retention'] } },
        '/v1/batch-processing/batches': { get: { summary: 'List batches', tags: ['Batch Processing'] }, post: { summary: 'Create batch', tags: ['Batch Processing'] } },
        '/v1/batch-processing/items': { get: { summary: 'Batch items', tags: ['Batch Processing'] } },
        '/admin/platform-metrics/alerts': { get: { summary: 'Metric alerts', tags: ['Platform Metrics'] } },
        '/v1/custom-domains/verifications': { get: { summary: 'Domain verifications', tags: ['Custom Domains'] } },
        '/v1/circuit-breaker/breakers': { get: { summary: 'List breakers', tags: ['Circuit Breaker'] }, post: { summary: 'Create breaker', tags: ['Circuit Breaker'] } },
        '/v1/circuit-breaker/events': { get: { summary: 'Breaker events', tags: ['Circuit Breaker'] } },
        '/v1/resource-allocation/allocations': { get: { summary: 'List allocations', tags: ['Resource Allocation'] }, post: { summary: 'Create allocation', tags: ['Resource Allocation'] } },
        '/v1/resource-allocation/pools': { get: { summary: 'Resource pools', tags: ['Resource Allocation'] } },
        '/admin/audit-trail/entries': { get: { summary: 'List audit entries', tags: ['Audit Trail'] }, post: { summary: 'Create entry', tags: ['Audit Trail'] } },
        '/admin/audit-trail/policies': { get: { summary: 'Audit policies', tags: ['Audit Trail'] } },
        '/v1/caching-config/configs': { get: { summary: 'List cache configs', tags: ['Caching Config'] }, post: { summary: 'Create config', tags: ['Caching Config'] } },
        '/v1/caching-config/stats': { get: { summary: 'Cache stats', tags: ['Caching Config'] } },
        '/admin/release-management/releases': { get: { summary: 'List releases', tags: ['Release Management'] }, post: { summary: 'Create release', tags: ['Release Management'] } },
        '/admin/release-management/notes': { get: { summary: 'Release notes', tags: ['Release Management'] } },
        '/v1/error-tracking/errors': { get: { summary: 'List errors', tags: ['Error Tracking'] }, post: { summary: 'Report error', tags: ['Error Tracking'] } },
        '/v1/error-tracking/rules': { get: { summary: 'Error rules', tags: ['Error Tracking'] } },
        '/v1/load-balancing/configs': { get: { summary: 'List LB configs', tags: ['Load Balancing'] }, post: { summary: 'Create config', tags: ['Load Balancing'] } },
        '/v1/load-balancing/targets': { get: { summary: 'LB targets', tags: ['Load Balancing'] } },
        '/v1/workflow-engine/workflows': { get: { summary: 'List workflows', tags: ['Workflow Engine'] }, post: { summary: 'Create workflow', tags: ['Workflow Engine'] } },
        '/v1/workflow-engine/executions': { get: { summary: 'Workflow executions', tags: ['Workflow Engine'] } },
        '/admin/security-scan/scans': { get: { summary: 'List scans', tags: ['Security Scan'] }, post: { summary: 'Create scan', tags: ['Security Scan'] } },
        '/admin/security-scan/findings': { get: { summary: 'Scan findings', tags: ['Security Scan'] } },
        '/admin/deployment-pipeline/pipelines': { get: { summary: 'List pipelines', tags: ['Deployment Pipeline'] }, post: { summary: 'Create pipeline', tags: ['Deployment Pipeline'] } },
        '/admin/deployment-pipeline/runs': { get: { summary: 'Pipeline runs', tags: ['Deployment Pipeline'] } },
        '/v1/performance-profiling/profiles': { get: { summary: 'List profiles', tags: ['Performance Profiling'] }, post: { summary: 'Create profile', tags: ['Performance Profiling'] } },
        '/v1/performance-profiling/baselines': { get: { summary: 'Perf baselines', tags: ['Performance Profiling'] } },
      },
      components: { securitySchemes: { bearer: { type: 'http', scheme: 'bearer' }, apiKey: { type: 'apiKey', in: 'header', name: 'X-API-Key' } } },
    });
  });

  // Catch-all 404
  routes.notFound((c) => {
    return notFound(`Route ${c.req.path} not found`);
  });

  return routes;
}
