// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pm/attribution-chart.tsx
// Bundled in _ds_bundle.js as window.AttributionChart

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface ChannelAttribution { channel: string; touches: number; revenue: number; roi: number; }
export interface AttributionChartProps extends React.HTMLAttributes<HTMLDivElement> { channels: ChannelAttribution[]; }

const AttributionChart = React.forwardRef<HTMLDivElement, AttributionChartProps>(
  ({ className, channels, ...props }, ref) => {
    const maxRevenue = Math.max(...channels.map((c) => c.revenue), 1);
    return (
      <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
        <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">MultiTouch Attribution</div>
        <div className="flex flexCol gap-[var(-SpacingSm)]">
          {channels.map((ch, i) => (
            <div key={i} className="flex itemsCenter gap-[var(-SpacingMd)]">
              <span className="w20 text-[var(-FontXs)] text-[var(-TextSecondary)] truncate">{ch.channel}</span>
              <div className="flex1 h4 rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] overflowHidden">
                <div className="hFull rounded-[var(-RadiusSm)] bg-[var(-ModelGemma)]/60" style={{ width: `${(ch.revenue / maxRevenue) * 100}%` }} />
              </div>
              <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w16 textRight">{ch.roi.toFixed(1)}x ROI</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
);
AttributionChart.displayName = "AttributionChart";
export { AttributionChart };
