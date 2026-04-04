"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface FunnelStage { name: string; value: number; count: number; }
export interface PipelineFunnelProps extends React.HTMLAttributes<HTMLDivElement> { stages: FunnelStage[]; }

const PipelineFunnel = React.forwardRef<HTMLDivElement, PipelineFunnelProps>(
  ({ className, stages, ...props }, ref) => {
    const max = Math.max(...stages.map((s) => s.value), 1);
    return (
      <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
        <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Revenue Funnel</div>
        <div className="flex flex-col gap-[var(--spacing-sm)]">
          {stages.map((stage, i) => {
            const width = Math.round((stage.value / max) * 100);
            return (
              <div key={i} className="flex items-center gap-[var(--spacing-md)]">
                <span className="w-20 text-[var(--font-xs)] text-[var(--text-secondary)] text-right">{stage.name}</span>
                <div className="flex-1 h-6 rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] overflow-hidden">
                  <div className="h-full rounded-[var(--radius-sm)] bg-[var(--accent-teal-500)]/60 flex items-center px-2 transition-all" style={{ width: `${width}%` }}>
                    <span className="font-mono text-[var(--font-xs)] text-[var(--text-primary)]">${(stage.value / 1000).toFixed(0)}K</span>
                  </div>
                </div>
                <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)] w-8 text-right">{stage.count}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
);
PipelineFunnel.displayName = "PipelineFunnel";
export { PipelineFunnel };
