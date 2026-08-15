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
        "flex flexCol gap-[var(-Spacing2)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing5)]",
        className
      )}
      ref={ref}
      {...props}
    >
      <span className="text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">{label}</span>
      <div className="flex itemsEnd justifyBetween gap-[var(-Spacing4)]">
        <span className="fontMono text-[var(-FontSize3xl)] fontBold text-[var(-TextPrimary)] leadingNone">
          {value}
        </span>
        {sparkline && <div className="h8 w20">{sparkline}</div>}
      </div>
      {trend && trendValue && (
        <div className="flex itemsCenter gap1">
          <span
            className={cn(
              "text-[var(-FontSizeSm)] fontMedium",
              trend === "up" && "text-[var(-ColorSuccess500)]",
              trend === "down" && "text-[var(-ColorDanger500)]",
              trend === "flat" && "text-[var(-TextTertiary)]"
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
