"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface ChannelAttribution { channel: string; touches: number; revenue: number; roi: number; }
export interface AttributionChartProps extends React.HTMLAttributes<HTMLDivElement> { channels: ChannelAttribution[]; }

const AttributionChart = React.forwardRef<HTMLDivElement, AttributionChartProps>(
  ({ className, channels, ...props }, ref) => {
    const maxRevenue = Math.max(...channels.map((c) => c.revenue), 1);
    return (
      <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
        <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Multi-Touch Attribution</div>
        <div className="flex flex-col gap-[var(--spacing-sm)]">
          {channels.map((ch, i) => (
            <div key={i} className="flex items-center gap-[var(--spacing-md)]">
              <span className="w-20 text-[var(--font-xs)] text-[var(--text-secondary)] truncate">{ch.channel}</span>
              <div className="flex-1 h-4 rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] overflow-hidden">
                <div className="h-full rounded-[var(--radius-sm)] bg-[var(--model-gemma)]/60" style={{ width: `${(ch.revenue / maxRevenue) * 100}%` }} />
              </div>
              <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)] w-16 text-right">{ch.roi.toFixed(1)}x ROI</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
);
AttributionChart.displayName = "AttributionChart";
export { AttributionChart };
