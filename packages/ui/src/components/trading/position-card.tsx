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
        "flex flex-col gap-[var(--spacing-3)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-secondary)] p-[var(--spacing-4)]",
        className
      )}
      ref={ref}
      {...props}
    >
      <p className="text-[var(--font-size-sm)] font-medium text-[var(--text-primary)] leading-snug">
        {question}
      </p>
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)]">Probability</span>
          <span className="font-mono text-[var(--font-size-xl)] font-bold text-[var(--text-primary)]">
            {probability}%
          </span>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)]">Position</span>
          <span className="font-mono text-[var(--font-size-sm)] text-[var(--text-secondary)]">
            ${positionSize.toLocaleString()}
          </span>
        </div>
      </div>
      <div className="flex items-center justify-between border-t border-[var(--border-default)] pt-[var(--spacing-2)]">
        <span
          className={cn(
            "font-mono text-[var(--font-size-sm)] font-semibold",
            unrealizedPnl >= 0 ? "text-[var(--color-gain)]" : "text-[var(--color-loss)]"
          )}
        >
          {unrealizedPnl >= 0 ? "+" : ""}{unrealizedPnl.toFixed(2)}
        </span>
        {sparkline && <div className="h-6 w-16">{sparkline}</div>}
      </div>
    </div>
  )
);
PositionCard.displayName = "PositionCard";

export { PositionCard };
