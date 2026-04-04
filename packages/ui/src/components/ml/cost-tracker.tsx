"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface ModelCost { model: string; requests: number; cost: number; color: string; }
export interface CostTrackerProps extends React.HTMLAttributes<HTMLDivElement> { models: ModelCost[]; budget: number; }

const CostTracker = React.forwardRef<HTMLDivElement, CostTrackerProps>(
  ({ className, models, budget, ...props }, ref) => {
    const totalCost = models.reduce((sum, m) => sum + m.cost, 0);
    const pct = Math.round((totalCost / budget) * 100);
    return (
      <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
        <div className="flex items-center justify-between mb-[var(--spacing-md)]">
          <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Inference Cost</span>
          <span className={cn("font-mono text-[var(--font-sm)]", pct > 90 ? "text-[var(--status-error)]" : "text-[var(--text-secondary)]")}>${totalCost.toFixed(2)} / ${budget}</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-[var(--bg-tertiary)] mb-[var(--spacing-md)]">
          <div className={cn("h-full rounded-full transition-all", pct > 90 ? "bg-[var(--status-error)]" : pct > 70 ? "bg-[var(--status-warning)]" : "bg-[var(--accent-teal-500)]")} style={{ width: `${Math.min(pct, 100)}%` }} />
        </div>
        <div className="flex flex-col gap-[var(--spacing-xs)]">
          {models.map((m, i) => (
            <div key={i} className="flex items-center justify-between text-[var(--font-xs)]">
              <div className="flex items-center gap-[var(--spacing-sm)]">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: m.color }} />
                <span className="text-[var(--text-primary)]">{m.model}</span>
              </div>
              <div className="flex items-center gap-[var(--spacing-lg)]">
                <span className="text-[var(--text-muted)]">{m.requests.toLocaleString()} req</span>
                <span className="font-mono text-[var(--text-secondary)]">${m.cost.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
);
CostTracker.displayName = "CostTracker";
export { CostTracker };
