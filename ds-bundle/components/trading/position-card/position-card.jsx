// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/trading/position-card.tsx
// Bundled in _ds_bundle.js as window.PositionCard

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface PositionCardProps extends React.HTMLAttributes<HTMLDivElement> {
  question: string;
  probability: number;
  positionSize: number;
  unrealizedPnl: number;
  sparkline?: React.ReactNode;
}

const PositionCard = React.forwardRef<HTMLDivElement, PositionCardProps>(
  ({ className, question, probability, positionSize, unrealizedPnl, sparkline, ...props }, ref) => (
    <div
      className={cn(
        "flex flexCol gap-[var(-Spacing3)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] p-[var(-Spacing4)]",
        className
      )}
      ref={ref}
      {...props}
    >
      <p className="text-[var(-FontSizeSm)] fontMedium text-[var(-TextPrimary)] leadingSnug">
        {question}
      </p>
      <div className="flex itemsCenter justifyBetween">
        <div className="flex flexCol">
          <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">Probability</span>
          <span className="fontMono text-[var(-FontSizeXl)] fontBold text-[var(-TextPrimary)]">
            {probability}%
          </span>
        </div>
        <div className="flex flexCol itemsEnd">
          <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">Position</span>
          <span className="fontMono text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
            ${positionSize.toLocaleString()}
          </span>
        </div>
      </div>
      <div className="flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-Spacing2)]">
        <span
          className={cn(
            "fontMono text-[var(-FontSizeSm)] fontSemibold",
            unrealizedPnl >= 0 ? "text-[var(-ColorGain)]" : "text-[var(-ColorLoss)]"
          )}
        >
          {unrealizedPnl >= 0 ? "+" : ""}{unrealizedPnl.toFixed(2)}
        </span>
        {sparkline && <div className="h6 w16">{sparkline}</div>}
      </div>
    </div>
  )
);
PositionCard.displayName = "PositionCard";

export { PositionCard };
