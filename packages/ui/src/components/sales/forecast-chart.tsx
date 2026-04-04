"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ForecastPoint { month: string; actual: number; forecast: number; }
export interface ForecastChartProps extends React.HTMLAttributes<HTMLDivElement> { data: ForecastPoint[]; target: number; }
const ForecastChart = React.forwardRef<HTMLDivElement, ForecastChartProps>(({ className, data, target, ...props }, ref) => {
  const max = Math.max(...data.map(d => Math.max(d.actual, d.forecast)), target);
  return (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="flex items-center justify-between mb-[var(--spacing-md)]"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Revenue Forecast</span><span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)]">Target: ${(target/1000).toFixed(0)}K</span></div>
      <div className="flex items-end gap-[var(--spacing-xs)] h-24">{data.map((d, i) => (<div key={i} className="flex-1 flex flex-col items-center gap-0.5"><div className="w-full flex gap-0.5"><div className="flex-1 bg-[var(--accent-teal-500)]/60 rounded-t-[var(--radius-sm)]" style={{ height: `${(d.actual / max) * 80}px` }} /><div className="flex-1 bg-[var(--model-deepseek)]/40 rounded-t-[var(--radius-sm)]" style={{ height: `${(d.forecast / max) * 80}px` }} /></div><span className="text-[var(--font-xs)] text-[var(--text-muted)]">{d.month}</span></div>))}</div>
    </div>
  );
});
ForecastChart.displayName = "ForecastChart";
export { ForecastChart };
