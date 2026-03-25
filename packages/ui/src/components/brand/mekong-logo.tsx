"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MekongLogoProps extends React.SVGAttributes<SVGSVGElement> {
  size?: number;
}

const MekongLogo = React.forwardRef<SVGSVGElement, MekongLogoProps>(
  ({ className, size = 40, ...props }, ref) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={cn("text-current", className)}
      ref={ref}
      {...props}
    >
      <path
        d="M24 4 C24 4, 22 16, 14 24 C8 30, 4 36, 6 44"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M24 4 C24 4, 24 18, 24 28 C24 34, 24 38, 24 44"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M24 4 C24 4, 26 16, 34 24 C40 30, 44 36, 42 44"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M24 4 C24 4, 20 14, 10 20 C6 22, 2 28, 2 34"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
      <path
        d="M24 4 C24 4, 28 14, 38 20 C42 22, 46 28, 46 34"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.5"
      />
    </svg>
  )
);
MekongLogo.displayName = "MekongLogo";

export { MekongLogo };
