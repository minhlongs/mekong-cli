"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-[var(--radius-full)] px-2.5 py-0.5 text-[var(--font-size-xs)] font-medium transition-colors duration-[var(--duration-fast)]",
  {
    variants: {
      variant: {
        idle: "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
        running: "bg-[var(--color-info-500)]/15 text-[var(--color-info-500)]",
        success: "bg-[var(--color-success-500)]/15 text-[var(--color-success-500)]",
        failed: "bg-[var(--color-danger-500)]/15 text-[var(--color-danger-500)]",
        warning: "bg-[var(--color-warning-500)]/15 text-[var(--color-warning-500)]",
        gain: "bg-[var(--color-gain)]/15 text-[var(--color-gain)]",
        loss: "bg-[var(--color-loss)]/15 text-[var(--color-loss)]",
      },
    },
    defaultVariants: { variant: "idle" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => (
    <span className={cn(badgeVariants({ variant, className }))} ref={ref} {...props} />
  )
);
Badge.displayName = "Badge";

export { Badge, badgeVariants };
