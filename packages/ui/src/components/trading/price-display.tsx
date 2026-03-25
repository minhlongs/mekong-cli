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
          "font-mono text-[var(--font-size-lg)] font-bold tabular-nums transition-colors duration-[var(--duration-fast)]",
          direction === "up" && "text-[var(--color-gain)]",
          direction === "down" && "text-[var(--color-loss)]",
          direction === "flat" && "text-[var(--text-primary)]",
          flash && "scale-105",
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
