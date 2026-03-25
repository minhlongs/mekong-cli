"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface CreditGaugeProps extends React.HTMLAttributes<HTMLDivElement> {
  used: number;
  total: number;
  tier: string;
}

const CreditGauge = React.forwardRef<HTMLDivElement, CreditGaugeProps>(
  ({ className, used, total, tier, ...props }, ref) => {
    const percentage = Math.min((used / total) * 100, 100);
    const radius = 44;
    const circumference = 2 * Math.PI * radius;
    const arcLength = circumference * 0.75;
    const offset = arcLength - (percentage / 100) * arcLength;

    const color =
      percentage > 90 ? "var(--color-danger-500)"
      : percentage > 70 ? "var(--color-warning-500)"
      : "var(--accent)";

    return (
      <div className={cn("flex flex-col items-center gap-[var(--spacing-2)]", className)} ref={ref} {...props}>
        <div className="relative">
          <svg width="120" height="100" viewBox="0 0 120 100">
            <circle
              cx="60" cy="60" r={radius}
              fill="none"
              stroke="var(--bg-tertiary)"
              strokeWidth="8"
              strokeDasharray={`${arcLength} ${circumference}`}
              strokeLinecap="round"
              transform="rotate(135 60 60)"
            />
            <circle
              cx="60" cy="60" r={radius}
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeDasharray={`${arcLength} ${circumference}`}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform="rotate(135 60 60)"
              className="transition-all duration-[var(--duration-slow)]"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center pt-2">
            <span className="font-mono text-[var(--font-size-2xl)] font-bold text-[var(--text-primary)]">
              {total - used}
            </span>
            <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)]">remaining</span>
          </div>
        </div>
        <span className="rounded-[var(--radius-full)] bg-[var(--accent)]/15 px-2.5 py-0.5 text-[var(--font-size-xs)] font-semibold text-[var(--accent)]">
          {tier}
        </span>
      </div>
    );
  }
);
CreditGauge.displayName = "CreditGauge";

export { CreditGauge };
