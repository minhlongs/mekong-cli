"use client";

import * as React from "react";
import { cn } from "../lib/utils";

export interface CreditMeterProps extends React.HTMLAttributes<HTMLDivElement> {
  used: number;
  total: number;
  label?: string;
}

const CreditMeter = React.forwardRef<HTMLDivElement, CreditMeterProps>(
  ({ className, used, total, label, ...props }, ref) => {
    const percentage = Math.min((used / total) * 100, 100);
    const circumference = 2 * Math.PI * 40;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    const color =
      percentage > 90
        ? "var(--color-danger-500)"
        : percentage > 70
          ? "var(--color-warning-500)"
          : "var(--accent)";

    return (
      <div className={cn("flex flex-col items-center gap-2", className)} ref={ref} {...props}>
        <svg width="96" height="96" viewBox="0 0 96 96" className="-rotate-90">
          <circle
            cx="48" cy="48" r="40"
            fill="none"
            stroke="var(--bg-tertiary)"
            strokeWidth="6"
          />
          <circle
            cx="48" cy="48" r="40"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-[var(--duration-slow)]"
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="font-mono text-[var(--font-size-lg)] font-bold text-[var(--text-primary)]">
            {used}
          </span>
          <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)]">
            / {total}
          </span>
        </div>
        {label && (
          <span className="text-[var(--font-size-sm)] text-[var(--text-secondary)]">{label}</span>
        )}
      </div>
    );
  }
);
CreditMeter.displayName = "CreditMeter";

export { CreditMeter };
