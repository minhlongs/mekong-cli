"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const statusDotVariants = cva(
  "relative inlineBlock h2.5 w2.5 roundedFull",
  {
    variants: {
      status: {
        online: "bg-[var(-ColorSuccess500)]",
        degraded: "bg-[var(-ColorWarning500)]",
        error: "bg-[var(-ColorDanger500)]",
        offline: "bg-[var(-ColorNeutral400)]",
      },
      pulse: {
        true: "",
        false: "",
      },
    },
    defaultVariants: { status: "offline", pulse: false },
  }
);

export interface StatusDotProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusDotVariants> {}

const StatusDot = React.forwardRef<HTMLSpanElement, StatusDotProps>(
  ({ className, status, pulse, ...props }, ref) => (
    <span className={cn("relative inlineFlex", className)} ref={ref} {...props}>
      {pulse && status !== "offline" && (
        <span
          className={cn(
            "absolute inlineFlex hFull wFull animatePing roundedFull opacity75",
            status === "online" && "bg-[var(-ColorSuccess500)]",
            status === "degraded" && "bg-[var(-ColorWarning500)]",
            status === "error" && "bg-[var(-ColorDanger500)]"
          )}
        />
      )}
      <span className={cn(statusDotVariants({ status }))} />
    </span>
  )
);
StatusDot.displayName = "StatusDot";

export { StatusDot, statusDotVariants };
