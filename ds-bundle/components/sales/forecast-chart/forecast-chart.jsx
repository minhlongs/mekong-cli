// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/sales/forecast-chart.tsx
// Bundled in _ds_bundle.js as window.ForecastChart

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ForecastPoint { month: string; actual: number; forecast: number; }
export interface ForecastChartProps extends React.HTMLAttributes<HTMLDivElement> { data: ForecastPoint[]; target: number; }
const ForecastChart = React.forwardRef<HTMLDivElement, ForecastChartProps>(({ className, data, target, ...props }, ref) => {
  const max = Math.max(...data.map(d => Math.max(d.actual, d.forecast)), target);
  return (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="flex itemsCenter justifyBetween mb-[var(-SpacingMd)]"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Revenue Forecast</span><span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">Target: ${(target/1000).toFixed(0)}K</span></div>
      <div className="flex itemsEnd gap-[var(-SpacingXs)] h24">{data.map((d, i) => (<div key={i} className="flex1 flex flexCol itemsCenter gap0.5"><div className="wFull flex gap0.5"><div className="flex1 bg-[var(-AccentTeal500)]/60 roundedT-[var(-RadiusSm)]" style={{ height: `${(d.actual / max) * 80}px` }} /><div className="flex1 bg-[var(-ModelDeepseek)]/40 roundedT-[var(-RadiusSm)]" style={{ height: `${(d.forecast / max) * 80}px` }} /></div><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{d.month}</span></div>))}</div>
    </div>
  );
});
ForecastChart.displayName = "ForecastChart";
export { ForecastChart };
