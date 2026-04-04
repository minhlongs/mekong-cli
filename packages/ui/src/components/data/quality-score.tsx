"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface QualityDimension { name: string; score: number; status: "pass" | "warn" | "fail"; }
export interface QualityScoreProps extends React.HTMLAttributes<HTMLDivElement> {
  dimensions: QualityDimension[];
}

const statusColor = { pass: "var(--status-healthy)", warn: "var(--status-warning)", fail: "var(--status-error)" };

const QualityScore = React.forwardRef<HTMLDivElement, QualityScoreProps>(
  ({ className, dimensions, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Data Quality</div>
      <div className="flex flex-col gap-[var(--spacing-md)]">
        {dimensions.map((d, i) => (
          <div key={i} className="flex items-center gap-[var(--spacing-md)]">
            <span className="w-24 text-[var(--font-sm)] text-[var(--text-secondary)]">{d.name}</span>
            <div className="flex-1 h-2 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${d.score}%`, backgroundColor: statusColor[d.status] }} />
            </div>
            <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)] w-10 text-right">{d.score}%</span>
          </div>
        ))}
      </div>
    </div>
  )
);
QualityScore.displayName = "QualityScore";
export { QualityScore };
