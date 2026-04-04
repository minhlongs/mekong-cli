"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const resultBadge = cva("rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: {
    result: {
      winning: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]",
      losing: "bg-[var(--status-error)]/15 text-[var(--status-error)]",
      inconclusive: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]",
      running: "bg-[var(--model-qwen)]/15 text-[var(--model-qwen)]",
    },
  },
  defaultVariants: { result: "running" },
});

export interface ExperimentCardProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  hypothesis: string;
  variant: string;
  confidence: number;
  result: "winning" | "losing" | "inconclusive" | "running";
  sampleSize: number;
}

const ExperimentCard = React.forwardRef<HTMLDivElement, ExperimentCardProps>(
  ({ className, name, hypothesis, variant, confidence, result, sampleSize, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="flex items-center justify-between">
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">{name}</span>
        <span className={resultBadge({ result })}>{result}</span>
      </div>
      <p className="text-[var(--font-xs)] text-[var(--text-secondary)]">{hypothesis}</p>
      <div className="flex items-center gap-[var(--spacing-lg)] border-t border-[var(--border-default)] pt-[var(--spacing-sm)] text-[var(--font-xs)]">
        <span className="text-[var(--text-muted)]">Variant: {variant}</span>
        <span className="text-[var(--text-muted)]">n={sampleSize.toLocaleString()}</span>
        <span className="font-mono text-[var(--accent-teal-400)]">{confidence}% confidence</span>
      </div>
    </div>
  )
);
ExperimentCard.displayName = "ExperimentCard";
export { ExperimentCard };
