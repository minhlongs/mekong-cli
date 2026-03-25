"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const pipelineBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-[var(--radius-full)] px-3 py-1 text-[var(--font-size-xs)] font-semibold uppercase tracking-wider transition-all duration-[var(--duration-normal)]",
  {
    variants: {
      phase: {
        plan: "bg-[var(--color-info-500)]/15 text-[var(--color-info-500)]",
        execute: "bg-[var(--color-warning-500)]/15 text-[var(--color-warning-500)]",
        verify: "bg-[var(--color-success-500)]/15 text-[var(--color-success-500)]",
      },
      active: {
        true: "",
        false: "opacity-50",
      },
    },
    defaultVariants: { phase: "plan", active: false },
  }
);

export interface PipelineBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof pipelineBadgeVariants> {}

const PipelineBadge = React.forwardRef<HTMLSpanElement, PipelineBadgeProps>(
  ({ className, phase, active, ...props }, ref) => (
    <span className={cn(pipelineBadgeVariants({ phase, active, className }))} ref={ref} {...props}>
      {active && (
        <span
          className={cn(
            "h-1.5 w-1.5 animate-pulse rounded-full",
            phase === "plan" && "bg-[var(--color-info-500)]",
            phase === "execute" && "bg-[var(--color-warning-500)]",
            phase === "verify" && "bg-[var(--color-success-500)]"
          )}
        />
      )}
      {phase}
    </span>
  )
);
PipelineBadge.displayName = "PipelineBadge";

export { PipelineBadge, pipelineBadgeVariants };
