"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MekongWordmarkProps extends React.HTMLAttributes<HTMLDivElement> {
  showSubtitle?: boolean;
}

const MekongWordmark = React.forwardRef<HTMLDivElement, MekongWordmarkProps>(
  ({ className, showSubtitle = true, ...props }, ref) => (
    <div className={cn("flex flexCol", className)} ref={ref} {...props}>
      <span
        className="fontSans text-[var(-FontSize2xl)] fontBold tracking-[0.05em] text-[var(-TextPrimary)]"
        style={{ fontWeight: 700 }}
      >
        MEKONG
      </span>
      {showSubtitle && (
        <span
          className="text-[var(-FontSizeSm)] fontNormal trackingWide text-[var(-TextSecondary)]"
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
