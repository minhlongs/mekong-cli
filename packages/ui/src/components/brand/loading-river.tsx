"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface LoadingRiverProps extends React.SVGAttributes<SVGSVGElement> {
  size?: number;
}

const LoadingRiver = React.forwardRef<SVGSVGElement, LoadingRiverProps>(
  ({ className, size = 48, ...props }, ref) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={cn("text-[var(--accent)]", className)}
      ref={ref}
      {...props}
    >
      <style>{`
        @keyframes river-flow {
          0% { stroke-dashoffset: 80; }
          50% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: -80; }
        }
        .river-path {
          stroke-dasharray: 20 60;
          animation: river-flow 2s ease-in-out infinite;
        }
        .river-path-delay-1 { animation-delay: -0.4s; }
        .river-path-delay-2 { animation-delay: -0.8s; }
        @media (prefers-reduced-motion: reduce) {
          .river-path { animation: none; stroke-dasharray: none; }
        }
      `}</style>
      <path
        className="river-path"
        d="M24 4 C22 14, 16 20, 10 28 C6 34, 6 38, 8 44"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        className="river-path river-path-delay-1"
        d="M24 4 C24 14, 24 24, 24 34 C24 38, 24 40, 24 44"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        className="river-path river-path-delay-2"
        d="M24 4 C26 14, 32 20, 38 28 C42 34, 42 38, 40 44"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
);
LoadingRiver.displayName = "LoadingRiver";

export { LoadingRiver };
