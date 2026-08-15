/**
 * Core domain types for Mekong IDE report pages.
 * Contract-first: types are stable before any backend exists.
 */

// ─── Department Commands ────────────────────────────────────────────────────

/** A single command exposed by a department (e.g. /cook, /deploy). */
export interface DepartmentCommand {
  /** URL-safe slug matching the mekong command name */
  slug: string;
  /** Human-readable title */
  title: string;
  /** One-line description shown in department view */
  description: string;
  /** Mekong Credit Units consumed per successful execution */
  mcu: number;
  /** Optional layer classification */
  layer?: "engineering" | "business" | "founder" | "product" | "ops" | "studio";
}

// ─── Pricing ────────────────────────────────────────────────────────────────

/** A subscription tier in the MCU billing model. */
export interface PricingTier {
  id: string;
  name: string;
  /** Monthly price in USD cents */
  priceUsdCents: number;
  /** MCU credits granted per month */
  creditsPerMonth: number;
  /** Polar checkout URL */
  checkoutUrl: string;
  highlighted?: boolean;
  features: string[];
}

// ─── Missions ───────────────────────────────────────────────────────────────

/** Status values for a mission lifecycle. */
export type MissionStatus = "pending" | "running" | "completed" | "failed";

/** A mission represents one agent execution (plan → execute → verify). */
export interface Mission {
  id: string;
  title: string;
  status: MissionStatus;
  /** ISO-8601 timestamp */
  createdAt: string;
  /** ISO-8601 timestamp, undefined while running */
  completedAt?: string;
  /** MCU units consumed, undefined until completed */
  mcuUsed?: number;
}

// ─── Report Page ─────────────────────────────────────────────────────────────

/** Generic wrapper returned by report page data fetchers. */
export interface ReportPage<T> {
  data: T;
  /** Unix timestamp (ms) when data was last fetched/generated */
  fetchedAt: number;
  /** Whether data comes from live API vs. static mock */
  source: "api" | "mock";
}
