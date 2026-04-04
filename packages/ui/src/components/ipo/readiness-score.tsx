"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ReadinessCategory { name: string; score: number; weight: number; }
export interface ReadinessScoreProps extends React.HTMLAttributes<HTMLDivElement> { overall: number; categories: ReadinessCategory[]; target: number; }
const ReadinessScore = React.forwardRef<HTMLDivElement, ReadinessScoreProps>(({ className, overall, categories, target, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="flex items-center justify-between mb-[var(--spacing-md)]"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">IPO Readiness</span><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Target: {target}%</span></div>
    <div className={cn("font-mono text-[var(--font-3xl)] font-bold", overall >= target ? "text-[var(--status-healthy)]" : "text-[var(--status-warning)]")}>{overall}%</div>
    <div className="mt-[var(--spacing-md)] flex flex-col gap-[var(--spacing-xs)]">
      {categories.map((c, i) => (<div key={i} className="flex items-center gap-[var(--spacing-sm)]"><span className="w-24 text-[var(--font-xs)] text-[var(--text-secondary)]">{c.name}</span><div className="flex-1 h-1.5 rounded-full bg-[var(--bg-tertiary)] overflow-hidden"><div className="h-full rounded-full bg-[var(--accent-teal-500)]" style={{ width: `${c.score}%` }} /></div><span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)] w-8 text-right">{c.score}%</span></div>))}
    </div>
  </div>
));
ReadinessScore.displayName = "ReadinessScore";
export { ReadinessScore };
