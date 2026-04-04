"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface McuGaugeProps extends React.HTMLAttributes<HTMLDivElement> { used: number; total: number; tier: string; }
const McuGauge = React.forwardRef<HTMLDivElement, McuGaugeProps>(({ className, used, total, tier, ...props }, ref) => {
  const pct = Math.round((used / total) * 100);
  return (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="flex items-center justify-between mb-[var(--spacing-sm)]"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">MCU Credits</span><span className="text-[var(--font-xs)] text-[var(--text-muted)]">{tier}</span></div>
      <div className="font-mono text-[var(--font-2xl)] font-bold text-[var(--text-primary)]">{used}<span className="text-[var(--font-sm)] text-[var(--text-muted)]">/{total}</span></div>
      <div className="mt-[var(--spacing-sm)] h-2 w-full rounded-full bg-[var(--bg-tertiary)] overflow-hidden"><div className={cn("h-full rounded-full transition-all", pct > 90 ? "bg-[var(--status-error)]" : pct > 70 ? "bg-[var(--status-warning)]" : "bg-[var(--accent-teal-500)]")} style={{ width: `${pct}%` }} /></div>
    </div>
  );
});
McuGauge.displayName = "McuGauge";
export { McuGauge };
