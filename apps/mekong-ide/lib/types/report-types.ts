/**
 * Report system types — layout definitions, section schemas, mission result binding.
 * Used by UniversalReportRenderer to render any report from JSON config + data.
 */

/** Supported section rendering primitives */
export type SectionType = "kpi-grid" | "table" | "chart" | "text" | "list" | "json";

/** A single section in a report layout */
export interface LayoutSection {
  /** Render primitive to use */
  type: SectionType;
  /** Section heading shown above content */
  title?: string;
  /** Dot-notation path into MissionResult.result_data, e.g. "metrics.roi" */
  dataPath: string;
  /** For kpi-grid: number of columns (default 3) */
  columns?: number;
  /** Type-specific extra config */
  config?: Record<string, unknown>;
}

/** Full layout definition for one report type */
export interface LayoutDefinition {
  /** Unique slug matching command name, e.g. "marketing-campaign" */
  id: string;
  /** Human-readable title */
  title: string;
  /** Department slug for badge color, e.g. "marketing" */
  department: string;
  /** Ordered sections to render */
  sections: LayoutSection[];
}

/** A single KPI metric item rendered as a card */
export interface KpiItem {
  label: string;
  value: string | number;
  /** Positive/negative delta shown as trend indicator */
  delta?: string | number;
  /** Optional unit suffix, e.g. "%" or "$" */
  unit?: string;
}

/** Mission execution result from API */
export interface MissionResult {
  id: string;
  command: string;
  department: string;
  status: "success" | "error" | "running" | "pending";
  /** Arbitrary nested data — sections bind into this via dataPath */
  result_data: Record<string, unknown>;
  created_at: string;
}
