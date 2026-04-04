"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface IrMetricProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  value: string;
  target?: string;
  trend: "up" | "down" | "flat";
  period: string;
}

const IrMetric = React.forwardRef<HTMLDivElement, IrMetricProps>(
  ({ className, name, value, target, trend, period, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <span className="text-[var(--font-xs)] text-[var(--text-muted)] uppercase tracking-wider">{name}</span>
      <div className="flex items-end gap-[var(--spacing-sm)]">
        <span className="font-mono text-[var(--font-2xl)] font-bold text-[var(--text-primary)]">{value}</span>
        <span className={cn("text-[var(--font-sm)] font-medium", trend === "up" ? "text-[var(--status-healthy)]" : trend === "down" ? "text-[var(--status-error)]" : "text-[var(--text-muted)]")}>
          {trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"}
        </span>
      </div>
      <div className="flex items-center justify-between">
        {target && <span className="text-[var(--font-xs)] text-[var(--text-secondary)]">Target: {target}</span>}
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">{period}</span>
      </div>
    </div>
  )
);
IrMetric.displayName = "IrMetric";
export { IrMetric };
