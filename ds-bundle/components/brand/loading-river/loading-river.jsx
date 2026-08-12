// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/brand/loading-river.tsx
// Bundled in _ds_bundle.js as window.LoadingRiver

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
      className={cn("text-[var(-Accent)]", className)}
      ref={ref}
      {...props}
    >
      <style>{`
        @keyframes riverFlow {
          0% { strokeDashoffset: 80; }
          50% { strokeDashoffset: 0; }
          100% { strokeDashoffset: 80; }
        }
        .riverPath {
          strokeDasharray: 20 60;
          animation: riverFlow 2s easeInOut infinite;
        }
        .riverPathDelay1 { animationDelay: 0.4s; }
        .riverPathDelay2 { animationDelay: 0.8s; }
        @media (prefersReducedMotion: reduce) {
          .riverPath { animation: none; strokeDasharray: none; }
        }
      `}</style>
      <path
        className="riverPath"
        d="M24 4 C22 14, 16 20, 10 28 C6 34, 6 38, 8 44"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        className="riverPath riverPathDelay1"
        d="M24 4 C24 14, 24 24, 24 34 C24 38, 24 40, 24 44"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        className="riverPath riverPathDelay2"
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
