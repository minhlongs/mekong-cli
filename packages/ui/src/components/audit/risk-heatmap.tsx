"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface RiskHeatmapProps extends React.HTMLAttributes<HTMLDivElement> {
  data: { likelihood: number; impact: number; label: string }[];
}

const cellColors = [
  ["bg-[var(--status-healthy)]/20", "bg-[var(--status-healthy)]/30", "bg-[var(--status-warning)]/20", "bg-[var(--status-warning)]/30", "bg-[var(--status-error)]/20"],
  ["bg-[var(--status-healthy)]/30", "bg-[var(--status-warning)]/20", "bg-[var(--status-warning)]/30", "bg-[var(--status-error)]/20", "bg-[var(--status-error)]/30"],
  ["bg-[var(--status-warning)]/20", "bg-[var(--status-warning)]/30", "bg-[var(--status-error)]/20", "bg-[var(--status-error)]/30", "bg-[var(--status-error)]/40"],
  ["bg-[var(--status-warning)]/30", "bg-[var(--status-error)]/20", "bg-[var(--status-error)]/30", "bg-[var(--status-error)]/40", "bg-[var(--status-error)]/60"],
  ["bg-[var(--status-error)]/20", "bg-[var(--status-error)]/30", "bg-[var(--status-error)]/40", "bg-[var(--status-error)]/60", "bg-[var(--status-error)]/80"],
];

const RiskHeatmap = React.forwardRef<HTMLDivElement, RiskHeatmapProps>(
  ({ className, data, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Risk Heat Map</div>
      <div className="grid grid-cols-5 gap-1">
        {[4, 3, 2, 1, 0].map((row) =>
          [0, 1, 2, 3, 4].map((col) => {
            const items = data.filter((d) => d.likelihood === col + 1 && d.impact === row + 1);
            return (
              <div key={`${row}-${col}`} className={cn("flex h-12 items-center justify-center rounded-[var(--radius-sm)] text-[var(--font-xs)] text-[var(--text-primary)]", cellColors[row][col])}>
                {items.map((item) => item.label).join(", ")}
              </div>
            );
          })
        )}
      </div>
      <div className="mt-[var(--spacing-xs)] flex justify-between text-[var(--font-xs)] text-[var(--text-muted)]">
        <span>Low Likelihood</span><span>High Likelihood</span>
      </div>
    </div>
  )
);
RiskHeatmap.displayName = "RiskHeatmap";
export { RiskHeatmap };
