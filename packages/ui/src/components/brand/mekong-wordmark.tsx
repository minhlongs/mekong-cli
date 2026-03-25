"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MekongWordmarkProps extends React.HTMLAttributes<HTMLDivElement> {
  showSubtitle?: boolean;
}

const MekongWordmark = React.forwardRef<HTMLDivElement, MekongWordmarkProps>(
  ({ className, showSubtitle = true, ...props }, ref) => (
    <div className={cn("flex flex-col", className)} ref={ref} {...props}>
      <span
        className="font-sans text-[var(--font-size-2xl)] font-bold tracking-[0.05em] text-[var(--text-primary)]"
        style={{ fontWeight: 700 }}
      >
        MEKONG
      </span>
      {showSubtitle && (
        <span
          className="text-[var(--font-size-sm)] font-normal tracking-wide text-[var(--text-secondary)]"
          style={{ fontWeight: 400 }}
        >
          Binh Pháp Venture Studio
        </span>
      )}
    </div>
  )
);
MekongWordmark.displayName = "MekongWordmark";

export { MekongWordmark };
