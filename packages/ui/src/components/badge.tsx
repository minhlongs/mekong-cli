"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const badgeVariants = cva(
  "inlineFlex itemsCenter rounded-[var(-RadiusFull)] px2.5 py0.5 text-[var(-FontSizeXs)] fontMedium transitionColors duration-[var(-DurationFast)]",
  {
    variants: {
      variant: {
        idle: "bg-[var(-BgTertiary)] text-[var(-TextSecondary)]",
        running: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
        success: "bg-[var(-ColorSuccess500)]/15 text-[var(-ColorSuccess500)]",
        failed: "bg-[var(-ColorDanger500)]/15 text-[var(-ColorDanger500)]",
        warning: "bg-[var(-ColorWarning500)]/15 text-[var(-ColorWarning500)]",
        gain: "bg-[var(-ColorGain)]/15 text-[var(-ColorGain)]",
        loss: "bg-[var(-ColorLoss)]/15 text-[var(-ColorLoss)]",
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
