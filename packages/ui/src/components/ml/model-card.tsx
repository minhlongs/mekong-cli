"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const modelStatusBadge = cva("rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: {
    status: {
      serving: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]",
      canary: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]",
      shadow: "bg-[var(--model-deepseek)]/15 text-[var(--model-deepseek)]",
      retired: "bg-[var(--status-idle)]/15 text-[var(--status-idle)]",
    },
  },
  defaultVariants: { status: "serving" },
});

export interface ModelCardProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  version: string;
  status: "serving" | "canary" | "shadow" | "retired";
  latencyP99: number;
  costPer1k: number;
  driftScore: number;
}

const ModelCard = React.forwardRef<HTMLDivElement, ModelCardProps>(
  ({ className, name, version, status, latencyP99, costPer1k, driftScore, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-[var(--spacing-sm)]">
          <span className="text-[var(--font-md)] font-semibold text-[var(--text-primary)]">{name}</span>
          <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)]">v{version}</span>
        </div>
        <span className={modelStatusBadge({ status })}>{status}</span>
      </div>
      <div className="grid grid-cols-3 gap-[var(--spacing-md)] border-t border-[var(--border-default)] pt-[var(--spacing-sm)]">
        <div className="flex flex-col">
          <span className="text-[var(--font-xs)] text-[var(--text-muted)]">P99 Latency</span>
          <span className="font-mono text-[var(--font-sm)] text-[var(--text-primary)]">{latencyP99}ms</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[var(--font-xs)] text-[var(--text-muted)]">Cost/1K</span>
          <span className="font-mono text-[var(--font-sm)] text-[var(--text-primary)]">${costPer1k.toFixed(3)}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[var(--font-xs)] text-[var(--text-muted)]">Drift</span>
          <span className={cn("font-mono text-[var(--font-sm)]", driftScore > 0.1 ? "text-[var(--status-error)]" : "text-[var(--status-healthy)]")}>{driftScore.toFixed(3)}</span>
        </div>
      </div>
    </div>
  )
);
ModelCard.displayName = "ModelCard";
export { ModelCard };
