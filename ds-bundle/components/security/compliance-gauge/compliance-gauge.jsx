// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/security/compliance-gauge.tsx
// Bundled in _ds_bundle.js as window.ComplianceGauge

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
        ? "var(-StatusHealthy)"
        : pct >= 70
          ? "var(-StatusWarning)"
          : "var(-StatusError)";

    return (
      <div
        ref={ref}
        className={cn(
          "flex flexCol itemsCenter gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]",
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
            stroke="var(-BorderDefault)"
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
            transform="rotate(90 50 50)"
            style={{ transition: "strokeDashoffset 0.6s ease" }}
          />
          <text
            x="50"
            y="46"
            textAnchor="middle"
            fill="var(-TextPrimary)"
            fontSize="var(-FontXl)"
            fontWeight="bold"
            fontFamily="var(-FontFamilyMono)"
          >
            {pct}%
          </text>
          <text
            x="50"
            y="62"
            textAnchor="middle"
            fill="var(-TextMuted)"
            fontSize="var(-FontXs)"
            fontFamily="var(-FontFamilySans)"
          >
            {score}/{maxScore}
          </text>
        </svg>
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">
          {framework}