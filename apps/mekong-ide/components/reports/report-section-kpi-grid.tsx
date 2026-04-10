/**
 * KPI grid section — renders an array of KpiItem as MD3-styled cards in a CSS grid.
 * Used by UniversalReportRenderer for sections of type "kpi-grid".
 */

import { Card } from "@/components/ds";
import type { KpiItem } from "@/lib/types/report-types";

interface KpiGridSectionProps {
  title?: string;
  items: KpiItem[];
  columns?: number;
}

/** Format delta with sign prefix and colour class */
function DeltaBadge({ delta }: { delta: string | number }) {
  const isNegative = String(delta).startsWith("-");
  return (
    <span
      style={{
        fontSize: "0.75rem",
        fontWeight: 500,
        color: isNegative ? "var(--status-danger)" : "var(--status-success)",
        marginTop: "0.25rem",
        display: "block",
      }}
    >
      {isNegative ? "" : "+"}
      {delta}
    </span>
  );
}

export function KpiGridSection({ title, items, columns = 3 }: KpiGridSectionProps) {
  const safeItems: KpiItem[] = Array.isArray(items) ? items : [];

  return (
    <section style={{ marginBottom: "1.5rem" }}>
      {title && (
        <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          {title}
        </h2>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
          gap: "0.75rem",
        }}
      >
        {safeItems.map((item, i) => (
          <Card key={i}>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
              {item.label}
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.2 }}>
              {item.value}
              {item.unit && (
                <span style={{ fontSize: "0.875rem", fontWeight: 400, marginLeft: "0.125rem" }}>{item.unit}</span>
              )}
            </div>
            {item.delta !== undefined && <DeltaBadge delta={item.delta} />}
          </Card>
        ))}
      </div>
    </section>
  );
}
