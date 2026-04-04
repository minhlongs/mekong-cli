"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface EvalResult { name: string; passed: boolean; score: number; baseline: number; }
export interface EvalSuiteProps extends React.HTMLAttributes<HTMLDivElement> { results: EvalResult[]; }

const EvalSuite = React.forwardRef<HTMLDivElement, EvalSuiteProps>(
  ({ className, results, ...props }, ref) => {
    const passCount = results.filter((r) => r.passed).length;
    return (
      <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden", className)} {...props}>
        <div className="flex items-center justify-between border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]">
          <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Eval Suite</span>
          <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)]">{passCount}/{results.length} passed</span>
        </div>
        {results.map((r, i) => (
          <div key={i} className="flex items-center justify-between border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)] last:border-b-0 hover:bg-[var(--surface-hover)]">
            <div className="flex items-center gap-[var(--spacing-sm)]">
              <span className={cn("font-bold", r.passed ? "text-[var(--status-healthy)]" : "text-[var(--status-error)]")}>{r.passed ? "\u2713" : "\u2717"}</span>
              <span className="text-[var(--font-sm)] text-[var(--text-primary)]">{r.name}</span>
            </div>
            <div className="flex items-center gap-[var(--spacing-md)] font-mono text-[var(--font-xs)]">
              <span className="text-[var(--text-muted)]">baseline: {r.baseline.toFixed(2)}</span>
              <span className={cn(r.score >= r.baseline ? "text-[var(--status-healthy)]" : "text-[var(--status-error)]")}>{r.score.toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>
    );
  }
);
EvalSuite.displayName = "EvalSuite";
export { EvalSuite };
