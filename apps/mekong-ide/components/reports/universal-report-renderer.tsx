/**
 * UniversalReportRenderer — takes a LayoutDefinition + MissionResult and renders
 * a complete report page by mapping each section to the correct primitive component.
 * Replaces the need for 316 individual page components.
 */

"use client";
import { Badge } from "@/components/ds";
import type { BadgeVariant } from "@/lib/types";
import type { LayoutDefinition, LayoutSection, MissionResult, KpiItem } from "@/lib/types/report-types";
import { KpiGridSection } from "./report-section-kpi-grid";
import { TableSection } from "./report-section-table";
import { TextSection } from "./report-section-text";
import { ReportFallbackJson } from "./report-fallback-json";

interface Props {
  layout: LayoutDefinition | null;
  data: MissionResult;
  loading?: boolean;
}

/** Safe dot-notation path resolver: "metrics.roi" into nested object */
function resolveDataPath(obj: unknown, path: string): unknown {
  return path.split(".").reduce((acc: unknown, key: string) => {
    if (acc !== null && acc !== undefined && typeof acc === "object") {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

/** Department slug → badge variant fallback map */
const DEPT_BADGE_MAP: Record<string, BadgeVariant> = {
  marketing: "info",
  finance: "success",
  sales: "trading",
  hr: "architect",
  compliance: "audit",
  engineering: "reasoning",
};

function departmentBadge(dept: string): BadgeVariant {
  return DEPT_BADGE_MAP[dept.toLowerCase()] ?? "info";
}

/** Skeleton placeholder shown while data is loading */
function ReportSkeleton() {
  return (
    <div style={{ padding: "1.5rem" }}>
      {[120, 80, 200].map((w, i) => (
        <div
          key={i}
          style={{
            height: "1rem",
            width: `${w}px`,
            background: "var(--border-subtle)",
            borderRadius: "0.25rem",
            marginBottom: "0.75rem",
            animation: "pulse 1.5s infinite",
          }}
        />
      ))}
    </div>
  );
}

/** Dispatch one section to correct renderer */
function ReportSection({ section, resultData }: { section: LayoutSection; resultData: Record<string, unknown> }) {
  const value = resolveDataPath(resultData, section.dataPath);

  switch (section.type) {
    case "kpi-grid":
      return (
        <KpiGridSection
          title={section.title}
          items={value as KpiItem[]}
          columns={section.columns}
        />
      );
    case "table":
      return (
        <TableSection
          title={section.title}
          rows={value as Record<string, unknown>[]}
          columnKeys={section.config?.columns as string[] | undefined}
        />
      );
    case "text":
    case "list":
      return <TextSection title={section.title} content={value} />;
    case "chart":
      // Charts deferred to Phase 5 — render table as fallback
      return (
        <TableSection
          title={section.title ? `${section.title} (chart pending)` : undefined}
          rows={Array.isArray(value) ? (value as Record<string, unknown>[]) : []}
        />
      );
    default:
      return <ReportFallbackJson data={value} label={section.title} />;
  }
}

export function UniversalReportRenderer({ layout, data, loading }: Props) {
  if (loading) return <ReportSkeleton />;

  if (!layout) {
    return (
      <div style={{ padding: "1.5rem" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "1rem" }}>
          No layout defined for command <strong>{data.command}</strong>. Showing raw output.
        </p>
        <ReportFallbackJson data={data.result_data} />
      </div>
    );
  }

  const createdAt = new Date(data.created_at).toLocaleString();

  return (
    <div style={{ padding: "1.5rem", maxWidth: "1200px" }}>
      {/* Report header */}
      <div style={{ marginBottom: "1.5rem", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.375rem" }}>
            {layout.title}
          </h1>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Badge variant={departmentBadge(layout.department)} label={layout.department} />
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{createdAt}</span>
          </div>
        </div>
        <Badge
          variant={data.status === "success" ? "success" : data.status === "error" ? "danger" : "warning"}
          label={data.status}
          dot
        />
      </div>

      {/* Sections */}
      {layout.sections.map((section, i) => (
        <ReportSection key={i} section={section} resultData={data.result_data} />
      ))}
    </div>
  );
}
