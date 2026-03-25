"use client";

import * as React from "react";
import { cn } from "../lib/utils";

export interface KpiCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  trend?: "up" | "down" | "flat";
  trendValue?: string;
  sparkline?: React.ReactNode;
}

const KpiCard = React.forwardRef<HTMLDivElement, KpiCardProps>(
  ({ className, label, value, trend, trendValue, sparkline, ...props }, ref) => (
    <div
      className={cn(
        "flex flex-col gap-[var(--spacing-2)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-[var(--spacing-5)]",
        className
      )}
      ref={ref}
      {...props}
    >
      <span className="text-[var(--font-size-sm)] text-[var(--text-secondary)]">{label}</span>
      <div className="flex items-end justify-between gap-[var(--spacing-4)]">
        <span className="font-mono text-[var(--font-size-3xl)] font-bold text-[var(--text-primary)] leading-none">
          {value}
        </span>
        {sparkline && <div className="h-8 w-20">{sparkline}</div>}
      </div>
      {trend && trendValue && (
        <div className="flex items-center gap-1">
          <span
            className={cn(
              "text-[var(--font-size-sm)] font-medium",
              trend === "up" && "text-[var(--color-success-500)]",
              trend === "down" && "text-[var(--color-danger-500)]",
              trend === "flat" && "text-[var(--text-tertiary)]"
            )}
          >
            {trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"} {trendValue}
          </span>
        </div>
      )}
    </div>
  )
);
KpiCard.displayName = "KpiCard";

export { KpiCard };
