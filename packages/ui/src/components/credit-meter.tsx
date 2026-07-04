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
        ? "var(-ColorDanger500)"
        : percentage > 70
          ? "var(-ColorWarning500)"
          : "var(-Accent)";

    return (
      <div className={cn("flex flexCol itemsCenter gap2", className)} ref={ref} {...props}>
        <svg width="96" height="96" viewBox="0 0 96 96" className="Rotate90">
          <circle
            cx="48" cy="48" r="40"
            fill="none"
            stroke="var(-BgTertiary)"
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
            className="transitionAll duration-[var(-DurationSlow)]"
          />
        </svg>
        <div className="absolute flex flexCol itemsCenter">
          <span className="fontMono text-[var(-FontSizeLg)] fontBold text-[var(-TextPrimary)]">
            {used}
          </span>
          <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">
            / {total}
          </span>
        </div>
        {label && (
          <span className="text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">{label}</span>
        )}
      </div>
    );
  }
);
CreditMeter.displayName = "CreditMeter";

export { CreditMeter };
