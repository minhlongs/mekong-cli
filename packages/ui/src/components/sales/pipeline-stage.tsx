"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface PipelineStageProps extends React.HTMLAttributes<HTMLDivElement> { stage: string; count: number; value: number; }
const PipelineStage = React.forwardRef<HTMLDivElement, PipelineStageProps>(({ className, stage, count, value, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col items-center gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-md)]", className)} {...props}>
    <span className="text-[var(--font-xs)] text-[var(--text-muted)] uppercase tracking-wider">{stage}</span>
    <span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">{count}</span>
    <span className="font-mono text-[var(--font-xs)] text-[var(--accent-teal-400)]">${(value / 1000).toFixed(0)}K</span>
  </div>
));
PipelineStage.displayName = "PipelineStage";
export { PipelineStage };
