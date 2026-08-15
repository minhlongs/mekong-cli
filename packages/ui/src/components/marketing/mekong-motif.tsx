"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MekongMotifProps extends React.SVGAttributes<SVGSVGElement> {
  variant?: "horizontal" | "radial";
}

const MekongMotif = React.forwardRef<SVGSVGElement, MekongMotifProps>(
  ({ className, variant = "horizontal", ...props }, ref) => {
    if (variant === "radial") {
      return (
        <svg
          className={cn("text-[var(--accent)]", className)}
          viewBox="0 0 200 200"
          fill="none"
          ref={ref}
          {...props}
        >
          <g stroke="currentColor" strokeWidth="0.5" opacity="0.15">
            {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => (
              <path
                key={angle}
                d={`M100,100 Q${100 + 30 * Math.cos((angle * Math.PI) / 180)},${100 + 30 * Math.sin((angle * Math.PI) / 180)} ${100 + 80 * Math.cos(((angle + 10) * Math.PI) / 180)},${100 + 80 * Math.sin(((angle + 10) * Math.PI) / 180)}`}
              />
            ))}
          </g>
        </svg>
      );
    }

    return (
      <svg
        className={cn("text-[var(--accent)]", className)}
        viewBox="0 0 400 100"
        fill="none"
        ref={ref}
        {...props}
      >
        <g stroke="currentColor" strokeWidth="0.5" opacity="0.15">
          <path d="M200,10 Q160,30 100,50 Q60,65 20,90" />
          <path d="M200,10 Q190,35 180,50 Q170,65 160,90" />
          <path d="M200,10 Q210,30 230,50 Q260,70 300,90" />
          <path d="M200,10 Q220,25 260,40 Q320,60 380,80" />
          <path d="M200,10 Q195,40 200,55 Q205,70 200,90" />
        </g>
      </svg>
    );
  }
);
MekongMotif.displayName = "MekongMotif";

export { MekongMotif };
