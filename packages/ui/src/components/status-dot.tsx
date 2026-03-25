"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const statusDotVariants = cva(
  "relative inline-block h-2.5 w-2.5 rounded-full",
  {
    variants: {
      status: {
        online: "bg-[var(--color-success-500)]",
        degraded: "bg-[var(--color-warning-500)]",
        error: "bg-[var(--color-danger-500)]",
        offline: "bg-[var(--color-neutral-400)]",
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
    <span className={cn("relative inline-flex", className)} ref={ref} {...props}>
      {pulse && status !== "offline" && (
        <span
          className={cn(
            "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
            status === "online" && "bg-[var(--color-success-500)]",
            status === "degraded" && "bg-[var(--color-warning-500)]",
            status === "error" && "bg-[var(--color-danger-500)]"
          )}
        />
      )}
      <span className={cn(statusDotVariants({ status }))} />
    </span>
  )
);
StatusDot.displayName = "StatusDot";

export { StatusDot, statusDotVariants };
