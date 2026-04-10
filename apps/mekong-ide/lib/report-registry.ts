/**
 * Report Registry — maps command slugs to LayoutDefinition objects.
 * Statically imports all 5 pre-loaded layouts so they are bundled at compile time
 * (compatible with Next.js static export — no filesystem access at runtime).
 */

import type { LayoutDefinition } from "@/lib/types/report-types";

// Pre-load all 5 layout JSON files as static imports
import marketingCampaign from "./report-layouts/marketing-campaign.json";
import financeBudgetPlan from "./report-layouts/finance-budget-plan.json";
import salesPipeline from "./report-layouts/sales-pipeline.json";
import complianceAudit from "./report-layouts/compliance-audit.json";
import hrReview from "./report-layouts/hr-review.json";

/** All registered layouts indexed by command slug */
const REGISTRY: Record<string, LayoutDefinition> = {
  "marketing-campaign": marketingCampaign as LayoutDefinition,
  "finance-budget-plan": financeBudgetPlan as LayoutDefinition,
  "sales-pipeline": salesPipeline as LayoutDefinition,
  "compliance-audit": complianceAudit as LayoutDefinition,
  "hr-review": hrReview as LayoutDefinition,
};

/**
 * Get layout definition for a given command slug.
 * Returns null if no layout is registered for that command.
 */
export function getLayout(commandSlug: string): LayoutDefinition | null {
  return REGISTRY[commandSlug] ?? null;
}

/** List all available layout definitions */
export function listLayouts(): LayoutDefinition[] {
  return Object.values(REGISTRY);
}

/** List all registered command slugs */
export function listLayoutSlugs(): string[] {
  return Object.keys(REGISTRY);
}
