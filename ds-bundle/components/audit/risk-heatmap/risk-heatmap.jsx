// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/audit/risk-heatmap.tsx
// Bundled in _ds_bundle.js as window.RiskHeatmap

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface RiskHeatmapProps extends React.HTMLAttributes<HTMLDivElement> {
  data: { likelihood: number; impact: number; label: string }[];
}

const cellColors = [
  ["bg-[var(-StatusHealthy)]/20", "bg-[var(-StatusHealthy)]/30", "bg-[var(-StatusWarning)]/20", "bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20"],
  ["bg-[var(-StatusHealthy)]/30", "bg-[var(-StatusWarning)]/20", "bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30"],
  ["bg-[var(-StatusWarning)]/20", "bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30", "bg-[var(-StatusError)]/40"],
  ["bg-[var(-StatusWarning)]/30", "bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30", "bg-[var(-StatusError)]/40", "bg-[var(-StatusError)]/60"],
  ["bg-[var(-StatusError)]/20", "bg-[var(-StatusError)]/30", "bg-[var(-StatusError)]/40", "bg-[var(-StatusError)]/60", "bg-[var(-StatusError)]/80"],
];

const RiskHeatmap = React.forwardRef<HTMLDivElement, RiskHeatmapProps>(
  ({ className, data, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Risk Heat Map</div>
      <div className="grid gridCols5 gap1">
        {[4, 3, 2, 1, 0].map((row) =>
          [0, 1, 2, 3, 4].map((col) => {
            const items = data.filter((d) => d.likelihood === col + 1 && d.impact === row + 1);
            return (
              <div key={`${row}-${col}`} className={cn("flex h12 itemsCenter justifyCenter rounded-[var(-RadiusSm)] text-[var(-FontXs)] text-[var(-TextPrimary)]", cellColors[row][col])}>
                {items.map((item) => item.label).join(", ")}
              </div>
            );
          })
        )}
      </div>
      <div className="mt-[var(-SpacingXs)] flex justifyBetween text-[var(-FontXs)] text-[var(-TextMuted)]">
        <span>Low Likelihood</span><span>High Likelihood</span>
      </div>
    </div>
  )
);
RiskHeatmap.displayName = "RiskHeatmap";
export { RiskHeatmap };
