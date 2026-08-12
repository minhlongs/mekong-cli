// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/governance/ir-metric.tsx
// Bundled in _ds_bundle.js as window.IrMetric

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface IrMetricProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  value: string;
  target?: string;
  trend: "up" | "down" | "flat";
  period: string;
}

const IrMetric = React.forwardRef<HTMLDivElement, IrMetricProps>(
  ({ className, name, value, target, trend, period, ...props }, ref) => (
    <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingXs)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <span className="text-[var(-FontXs)] text-[var(-TextMuted)] uppercase trackingWider">{name}</span>
      <div className="flex itemsEnd gap-[var(-SpacingSm)]">
        <span className="fontMono text-[var(-Font2xl)] fontBold text-[var(-TextPrimary)]">{value}</span>
        <span className={cn("text-[var(-FontSm)] fontMedium", trend === "up" ? "text-[var(-StatusHealthy)]" : trend === "down" ? "text-[var(-StatusError)]" : "text-[var(-TextMuted)]")}>
          {trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"}
        </span>
      </div>
      <div className="flex itemsCenter justifyBetween">
        {target && <span className="text-[var(-FontXs)] text-[var(-TextSecondary)]">Target: {target}</span>}
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{period}</span>
      </div>
    </div>
  )
);
IrMetric.displayName = "IrMetric";
export { IrMetric };
