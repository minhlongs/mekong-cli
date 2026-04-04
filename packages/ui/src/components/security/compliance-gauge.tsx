"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface ComplianceGaugeProps extends React.HTMLAttributes<HTMLDivElement> {
  framework: "SOC2" | "SOX" | "ISO27001";
  score: number;
  maxScore: number;
}

const ComplianceGauge = React.forwardRef<HTMLDivElement, ComplianceGaugeProps>(
  ({ className, framework, score, maxScore, ...props }, ref) => {
    const pct = Math.round((score / maxScore) * 100);
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (pct / 100) * circumference;

    const color =
      pct >= 90
        ? "var(--status-healthy)"
        : pct >= 70
          ? "var(--status-warning)"
          : "var(--status-error)";

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col items-center gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]",
          className
        )}
        {...props}
      >
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="var(--border-default)"
            strokeWidth="8"
          />
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
          <text
            x="50"
            y="46"
            textAnchor="middle"
            fill="var(--text-primary)"
            fontSize="var(--font-xl)"
            fontWeight="bold"
            fontFamily="var(--font-family-mono)"
          >
            {pct}%
          </text>
          <text
            x="50"
            y="62"
            textAnchor="middle"
            fill="var(--text-muted)"
            fontSize="var(--font-xs)"
            fontFamily="var(--font-family-sans)"
          >
            {score}/{maxScore}
          </text>
        </svg>
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">
          {framework}
        </span>
      </div>
    );
  }
);
ComplianceGauge.displayName = "ComplianceGauge";

export { ComplianceGauge };
