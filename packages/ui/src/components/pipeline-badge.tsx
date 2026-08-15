"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const pipelineBadgeVariants = cva(
  "inlineFlex itemsCenter gap1.5 rounded-[var(-RadiusFull)] px3 py1 text-[var(-FontSizeXs)] fontSemibold uppercase trackingWider transitionAll duration-[var(-DurationNormal)]",
  {
    variants: {
      phase: {
        plan: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
        execute: "bg-[var(-ColorWarning500)]/15 text-[var(-ColorWarning500)]",
        verify: "bg-[var(-ColorSuccess500)]/15 text-[var(-ColorSuccess500)]",
      },
      active: {
        true: "",
        false: "opacity50",
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
            "h1.5 w1.5 animatePulse roundedFull",
            phase === "plan" && "bg-[var(-ColorInfo500)]",
            phase === "execute" && "bg-[var(-ColorWarning500)]",
            phase === "verify" && "bg-[var(-ColorSuccess500)]"
          )}
        />
      )}
      {phase}
    </span>
  )
);
PipelineBadge.displayName = "PipelineBadge";

export { PipelineBadge, pipelineBadgeVariants };
