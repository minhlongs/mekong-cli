// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/trading/order-book.tsx
// Bundled in _ds_bundle.js as window.OrderBook

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
      <div key={`${side}-${row.price}`} className="relative flex itemsCenter justifyBetween px3 py1">
        <div
          className={cn(
            "absolute insetY0 opacity15",
            side === "bid" ? "left0 bg-[var(-ColorBid)]" : "right0 bg-[var(-ColorAsk)]"
          )}
          style={{ width: `${(row.size / max) * 100}%` }}
        />
        <span className={cn(
          "relative z10 fontMono text-[var(-FontSizeSm)]",
          side === "bid" ? "text-[var(-ColorBid)]" : "text-[var(-ColorAsk)]"
        )}>
          {row.price.toFixed(2)}
        </span>
        <span className={cn(
          "relative z10 fontMono text-[var(-FontSizeSm)] text-[var(-TextSecondary)]",
          row.isBot && "underline decorationDotted"
        )}>
          {row.size.toLocaleString()}
        </span>
      </div>
    );

    return (
      <div
        className={cn(
          "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] overflowHidden",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px3 py2">
          <span className="text-[var(-FontSizeXs)] fontMedium text-[var(-TextSecondary)]">Price</span>
          <span className="text-[var(-FontSizeXs)] fontMedium text-[var(-TextSecondary)]">Size</span>
        </div>
        <div className="flex flexCol">
          {asks.slice().reverse().map((row) => renderRow(row, "ask"))}
          <div className="borderY border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 textCenter">
            <span className="text-[var(-FontSizeXs)] fontMedium text-[var(-TextTertiary)]">Spread</span>
          </div>
          {bids.map((row) => renderRow(row, "bid"))}
        </div>
      </div>
    );
  }
);
OrderBook.displayName = "OrderBook";

export { OrderBook };
