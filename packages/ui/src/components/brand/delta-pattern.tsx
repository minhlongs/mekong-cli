"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface DeltaPatternProps extends React.SVGAttributes<SVGSVGElement> {
  variant?: "horizontal" | "radial";
  opacity?: number;
}

const DeltaPattern = React.forwardRef<SVGSVGElement, DeltaPatternProps>(
  ({ className, variant = "horizontal", opacity = 0.04, ...props }, ref) => {
    if (variant === "radial") {
      return (
        <svg
          className={cn("pointer-events-none absolute inset-0 h-full w-full text-[var(--accent)]", className)}
          viewBox="0 0 400 400"
          fill="none"
          ref={ref}
          {...props}
        >
          <g stroke="currentColor" strokeWidth="0.5" opacity={opacity}>
            {Array.from({ length: 12 }, (_, i) => {
              const angle = (i * 30 * Math.PI) / 180;
              const cx = 200 + 60 * Math.cos(angle);
              const cy = 200 + 60 * Math.sin(angle);
              const ex = 200 + 180 * Math.cos(angle + 0.15);
              const ey = 200 + 180 * Math.sin(angle + 0.15);
              return <path key={i} d={`M200,200 Q${cx},${cy} ${ex},${ey}`} />;
            })}
          </g>
        </svg>
      );
    }

    return (
      <svg
        className={cn("pointer-events-none absolute inset-0 h-full w-full text-[var(--accent)]", className)}
        viewBox="0 0 800 120"
        fill="none"
        preserveAspectRatio="none"
        ref={ref}
        {...props}
      >
        <g stroke="currentColor" strokeWidth="0.5" opacity={opacity}>
          {Array.from({ length: 8 }, (_, i) => {
            const startX = 100 * i + 50;
            return (
              <React.Fragment key={i}>
                <path d={`M${startX},10 Q${startX - 20},40 ${startX - 40},60 Q${startX - 50},80 ${startX - 30},110`} />
                <path d={`M${startX},10 Q${startX},35 ${startX},60 Q${startX},85 ${startX},110`} />
                <path d={`M${startX},10 Q${startX + 20},40 ${startX + 40},60 Q${startX + 50},80 ${startX + 30},110`} />
              </React.Fragment>
            );
          })}
        </g>
      </svg>
    );
  }
);
DeltaPattern.displayName = "DeltaPattern";

export { DeltaPattern };
