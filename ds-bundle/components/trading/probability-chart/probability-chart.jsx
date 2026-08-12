// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/trading/probability-chart.tsx
// Bundled in _ds_bundle.js as window.ProbabilityChart

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface ProbabilityChartProps extends React.HTMLAttributes<HTMLDivElement> {
  data: { time: string; value: number }[];
  height?: number;
  color?: string;
}

const ProbabilityChart = React.forwardRef<HTMLDivElement, ProbabilityChartProps>(
  ({ className, data, height = 200, color, ...props }, ref) => {
    const chartColor = color ?? "var(-Accent)";
    const min = Math.min(...data.map((d) => d.value));
    const max = Math.max(...data.map((d) => d.value));
    const range = max - min || 1;

    const points = data.map((d, i) => {
      const x = (i / (data.length - 1)) * 100;
      const y = 100 - ((d.value - min) / range) * 100;
      return `${x},${y}`;
    }).join(" ");

    const areaPoints = `0,100 ${points} 100,100`;

    return (
      <div
        className={cn(
          "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing4)]",
          className
        )}
        ref={ref}
        style={{ height }}
        {...props}
      >
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="hFull wFull"
        >
          <polygon
            points={areaPoints}
            fill={chartColor}
            fillOpacity="0.1"
          />
          <polyline
            points={points}
            fill="none"
            stroke={chartColor}
            strokeWidth="1.5"
            vectorEffect="nonScalingStroke"
          />
        </svg>
      </div>
    );
  }
);
ProbabilityChart.displayName = "ProbabilityChart";

export { ProbabilityChart };
