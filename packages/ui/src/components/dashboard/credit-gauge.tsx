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
      percentage > 90 ? "var(-ColorDanger500)"
      : percentage > 70 ? "var(-ColorWarning500)"
      : "var(-Accent)";

    return (
      <div className={cn("flex flexCol itemsCenter gap-[var(-Spacing2)]", className)} ref={ref} {...props}>
        <div className="relative">
          <svg width="120" height="100" viewBox="0 0 120 100">
            <circle
              cx="60" cy="60" r={radius}
              fill="none"
              stroke="var(-BgTertiary)"
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
              className="transitionAll duration-[var(-DurationSlow)]"
            />
          </svg>
          <div className="absolute inset0 flex flexCol itemsCenter justifyCenter pt2">
            <span className="fontMono text-[var(-FontSize2xl)] fontBold text-[var(-TextPrimary)]">
              {total - used}
            </span>
            <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">remaining</span>
          </div>
        </div>
        <span className="rounded-[var(-RadiusFull)] bg-[var(-Accent)]/15 px2.5 py0.5 text-[var(-FontSizeXs)] fontSemibold text-[var(-Accent)]">
          {tier}
        </span>
      </div>
    );
  }
);
CreditGauge.displayName = "CreditGauge";

export { CreditGauge };
