/**
 * feature-map.ts — maps CLI command names to minimum required license tier
 */
import type { LicenseTier } from './types.js';
import { TIER_ORDER } from './types.js';

export interface FeatureEntry {
  command: string;
  minTier: LicenseTier;
  description: string;
}

/** Complete feature→tier map. Free commands are not listed (always allowed). */
export const FEATURE_MAP: FeatureEntry[] = [
  // Free tier (always allowed)
  { command: 'run',      minTier: 'free',       description: 'Run a natural language task' },
  { command: 'sop',      minTier: 'free',       description: 'Execute SOP files' },
  { command: 'status',   minTier: 'free',       description: 'Engine status' },
  { command: 'license',  minTier: 'free',       description: 'License management' },
  { command: 'usage',    minTier: 'free',       description: 'Usage statistics' },
  { command: 'help',     minTier: 'free',       description: 'Help and documentation' },

  // Starter tier ($49/mo)
  { command: 'crm',       minTier: 'starter',   description: 'CRM management' },
  { command: 'finance',   minTier: 'starter',   description: 'Finance tracking' },
  { command: 'dashboard', minTier: 'starter',   description: 'Business dashboard' },
  { command: 'cook',      minTier: 'starter',   description: 'Smart feature implementation' },
  { command: 'plan',      minTier: 'starter',   description: 'Implementation planning' },

  // Pro tier ($149/mo)
  { command: 'kaizen',        minTier: 'pro',   description: 'Kaizen analytics' },
  { command: 'marketplace',   minTier: 'pro',   description: 'SOP marketplace' },
  { command: 'plugin',        minTier: 'pro',   description: 'Plugin management' },
  { command: 'mcp',           minTier: 'pro',   description: 'MCP server management' },
  { command: 'deploy',        minTier: 'pro',   description: 'Production deployment' },
  { command: 'review',        minTier: 'pro',   description: 'Code review' },
  { command: 'raas validate', minTier: 'pro',   description: 'RaaS license validation' },
  { command: 'raas balance',  minTier: 'pro',   description: 'RaaS credit balance' },
  { command: 'raas tiers',    minTier: 'pro',   description: 'RaaS tier listing' },
  { command: 'cli list',      minTier: 'pro',   description: 'CLI provider discovery' },
  { command: 'cli switch',    minTier: 'pro',   description: 'Switch CLI provider' },
  { command: 'rd scan',       minTier: 'pro',   description: 'R&D community scan' },

  // Enterprise tier ($499/mo)
  { command: 'self-improve',      minTier: 'enterprise', description: 'AI self-improvement' },
  { command: 'agi status',        minTier: 'enterprise', description: 'AGI evolution metrics' },
  { command: 'agi evolve',        minTier: 'enterprise', description: 'Trigger AGI evolution' },
  { command: 'agi benchmark',     minTier: 'enterprise', description: 'Competitive benchmarking' },
  { command: 'solo start',        minTier: 'enterprise', description: 'Start SoloOS company' },
  { command: 'solo status',       minTier: 'enterprise', description: 'SoloOS company health' },
  { command: 'solo report',       minTier: 'enterprise', description: 'SoloOS daily report' },
  { command: 'vc pitch',          minTier: 'enterprise', description: 'VC pitch deck generator' },
  { command: 'vc dataroom',       minTier: 'enterprise', description: 'Virtual data room' },
  { command: 'vc compliance',     minTier: 'enterprise', description: 'ISO/SOC/GDPR compliance' },
  { command: 'vc exit',           minTier: 'enterprise', description: 'Exit strategy & valuation' },
  { command: 'swarm start',       minTier: 'enterprise', description: 'Multi-CLI swarm' },
  { command: 'swarm status',      minTier: 'enterprise', description: 'Swarm load balance' },
  { command: 'live-dashboard',    minTier: 'enterprise', description: 'Live terminal dashboard' },
  { command: 'rd report',         minTier: 'enterprise', description: 'R&D weekly report' },
  { command: 'raas onboard',      minTier: 'enterprise', description: 'Tenant onboarding' },
  { command: 'raas status',       minTier: 'enterprise', description: 'RaaS tenant status' },
  { command: 'raas health',       minTier: 'enterprise', description: 'RaaS system health' },
  { command: 'sales-analytics',   minTier: 'enterprise', description: 'Sales analytics & funnel' },
  { command: 'cto-brain',         minTier: 'enterprise', description: 'CTO brain management' },
];

/**
 * Returns true if `current` meets or exceeds `required` tier.
 * @param current - the user's current license tier
 * @param required - the minimum tier needed
 */
export function tierMeetsMinimum(current: LicenseTier, required: LicenseTier): boolean {
  return TIER_ORDER.indexOf(current) >= TIER_ORDER.indexOf(required);
}

/**
 * Returns the minimum tier required for a command, or 'free' if unknown.
 * @param command - CLI command name (e.g. 'kaizen', 'crm')
 */
export function getRequiredTier(command: string): LicenseTier {
  const entry = FEATURE_MAP.find(f => f.command === command);
  return entry?.minTier ?? 'free';
}
