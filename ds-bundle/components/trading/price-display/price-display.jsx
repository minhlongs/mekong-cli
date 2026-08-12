// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/trading/price-display.tsx
// Bundled in _ds_bundle.js as window.PriceDisplay

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface PriceDisplayProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number;
  previousValue?: number;
  currency?: string;
  decimals?: number;
}

const PriceDisplay = React.forwardRef<HTMLSpanElement, PriceDisplayProps>(
  ({ className, value, previousValue, currency = "$", decimals = 2, ...props }, ref) => {
    const direction = previousValue !== undefined
      ? value > previousValue ? "up" : value < previousValue ? "down" : "flat"
      : "flat";
    const [flash, setFlash] = React.useState(false);

    React.useEffect(() => {
      if (previousValue !== undefined && value !== previousValue) {
        setFlash(true);
        const timer = setTimeout(() => setFlash(false), 300);
        return () => clearTimeout(timer);
      }
    }, [value, previousValue]);

    return (
      <span
        className={cn(
          "fontMono text-[var(-FontSizeLg)] fontBold tabularNums transitionColors duration-[var(-DurationFast)]",
          direction === "up" && "text-[var(-ColorGain)]",
          direction === "down" && "text-[var(-ColorLoss)]",
          direction === "flat" && "text-[var(-TextPrimary)]",
          flash && "scale105",
          className
        )}
        ref={ref}
        {...props}
      >
        {currency}{value.toFixed(decimals)}
      </span>
    );
  }
);
PriceDisplay.displayName = "PriceDisplay";

export { PriceDisplay };
