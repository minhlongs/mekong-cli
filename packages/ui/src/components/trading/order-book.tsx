"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface OrderRow {
  price: number;
  size: number;
  isBot?: boolean;
}

export interface OrderBookProps extends React.HTMLAttributes<HTMLDivElement> {
  bids: OrderRow[];
  asks: OrderRow[];
  maxDepth?: number;
}

const OrderBook = React.forwardRef<HTMLDivElement, OrderBookProps>(
  ({ className, bids, asks, maxDepth, ...props }, ref) => {
    const max = maxDepth ?? Math.max(
      ...bids.map((b) => b.size),
      ...asks.map((a) => a.size),
      1
    );

    const renderRow = (row: OrderRow, side: "bid" | "ask") => (
      <div key={`${side}-${row.price}`} className="relative flex items-center justify-between px-3 py-1">
        <div
          className={cn(
            "absolute inset-y-0 opacity-15",
            side === "bid" ? "left-0 bg-[var(--color-bid)]" : "right-0 bg-[var(--color-ask)]"
          )}
          style={{ width: `${(row.size / max) * 100}%` }}
        />
        <span className={cn(
          "relative z-10 font-mono text-[var(--font-size-sm)]",
          side === "bid" ? "text-[var(--color-bid)]" : "text-[var(--color-ask)]"
        )}>
          {row.price.toFixed(2)}
        </span>
        <span className={cn(
          "relative z-10 font-mono text-[var(--font-size-sm)] text-[var(--text-secondary)]",
          row.isBot && "underline decoration-dotted"
        )}>
          {row.size.toLocaleString()}
        </span>
      </div>
    );

    return (
      <div
        className={cn(
          "rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="flex items-center justify-between border-b border-[var(--border-default)] px-3 py-2">
          <span className="text-[var(--font-size-xs)] font-medium text-[var(--text-secondary)]">Price</span>
          <span className="text-[var(--font-size-xs)] font-medium text-[var(--text-secondary)]">Size</span>
        </div>
        <div className="flex flex-col">
          {asks.slice().reverse().map((row) => renderRow(row, "ask"))}
          <div className="border-y border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-1 text-center">
            <span className="text-[var(--font-size-xs)] font-medium text-[var(--text-tertiary)]">Spread</span>
          </div>
          {bids.map((row) => renderRow(row, "bid"))}
        </div>
      </div>
    );
  }
);
OrderBook.displayName = "OrderBook";

export { OrderBook };
