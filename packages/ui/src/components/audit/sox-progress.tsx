"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface SoxProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  phases: { name: string; total: number; completed: number }[];
}

const SoxProgress = React.forwardRef<HTMLDivElement, SoxProgressProps>(
  ({ className, phases, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">SOX ICFR Progress</div>
      <div className="flex flex-col gap-[var(--spacing-md)]">
        {phases.map((phase, i) => {
          const pct = phase.total > 0 ? Math.round((phase.completed / phase.total) * 100) : 0;
          return (
            <div key={i} className="flex flex-col gap-[var(--spacing-xs)]">
              <div className="flex items-center justify-between">
                <span className="text-[var(--font-sm)] text-[var(--text-primary)]">{phase.name}</span>
                <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)]">{phase.completed}/{phase.total}</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
                <div className="h-full rounded-full bg-[var(--accent-teal-500)] transition-all duration-500" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  )
);
SoxProgress.displayName = "SoxProgress";
export { SoxProgress };
