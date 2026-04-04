"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const nodeStatus = cva("flex h-10 items-center justify-center rounded-[var(--radius-md)] px-[var(--spacing-md)] text-[var(--font-xs)] font-medium border", {
  variants: {
    status: {
      running: "border-[var(--accent-teal-500)] bg-[var(--accent-teal-500)]/10 text-[var(--accent-teal-400)] animate-pulse",
      success: "border-[var(--status-healthy)] bg-[var(--status-healthy)]/10 text-[var(--status-healthy)]",
      failed: "border-[var(--status-error)] bg-[var(--status-error)]/10 text-[var(--status-error)]",
      pending: "border-[var(--border-default)] bg-[var(--bg-tertiary)] text-[var(--text-muted)]",
    },
  },
  defaultVariants: { status: "pending" },
});

export interface DagNode { id: string; name: string; status: "running" | "success" | "failed" | "pending"; }
export interface PipelineDagProps extends React.HTMLAttributes<HTMLDivElement> {
  stages: DagNode[][];
}

const PipelineDag = React.forwardRef<HTMLDivElement, PipelineDagProps>(
  ({ className, stages, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Pipeline DAG</div>
      <div className="flex items-center gap-[var(--spacing-sm)]">
        {stages.map((stage, si) => (
          <React.Fragment key={si}>
            <div className="flex flex-col gap-[var(--spacing-xs)]">
              {stage.map((node) => (
                <div key={node.id} className={nodeStatus({ status: node.status })}>{node.name}</div>
              ))}
            </div>
            {si < stages.length - 1 && <div className="h-0.5 w-6 bg-[var(--border-default)]" />}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
);
PipelineDag.displayName = "PipelineDag";
export { PipelineDag };
