// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/finance/revenue-chart.tsx
// Bundled in _ds_bundle.js as window.RevenueChart

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface RevenueChartProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const RevenueChart = React.forwardRef<HTMLDivElement, RevenueChartProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Revenue</div>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{label || "Component ready"}</div>
  </div>
));
RevenueChart.displayName = "RevenueChart";
export { RevenueChart };
