"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface ActivityItem {
  id: string;
  timestamp: string;
  actionType: "buy" | "sell" | "hedge" | "rebalance";
  description: string;
  amount?: number;
}

export interface ActivityFeedProps extends React.HTMLAttributes<HTMLDivElement> {
  items: ActivityItem[];
  maxItems?: number;
}

const actionColors: Record<string, string> = {
  buy: "bg-[var(-ColorGain)]/15 text-[var(-ColorGain)]",
  sell: "bg-[var(-ColorLoss)]/15 text-[var(-ColorLoss)]",
  hedge: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
  rebalance: "bg-[var(-ColorWarning500)]/15 text-[var(-ColorWarning500)]",
};

const ActivityFeed = React.forwardRef<HTMLDivElement, ActivityFeedProps>(
  ({ className, items, maxItems = 20, ...props }, ref) => (
    <div
      className={cn(
        "flex flexCol overflowYAuto rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)]",
        className
      )}
      ref={ref}
      {...props}
    >
      <div className="sticky top0 borderB border-[var(-BorderDefault)] bg-[var(-BgPrimary)] px4 py2">
        <span className="text-[var(-FontSizeSm)] fontMedium text-[var(-TextSecondary)]">Activity</span>
      </div>
      {items.slice(0, maxItems).map((item) => (
        <div key={item.id} className="flex itemsCenter gap3 borderB border-[var(-BorderDefault)] px4 py2.5 last:border0">
          <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)] tabularNums whitespaceNowrap">
            {item.timestamp}
          </span>
          <span className={cn(
            "rounded-[var(-RadiusFull)] px2 py0.5 text-[0.625rem] fontSemibold uppercase",
            actionColors[item.actionType]
          )}>
            {item.actionType}
          </span>
          <span className="flex1 truncate text-[var(-FontSizeSm)] text-[var(-TextPrimary)]">
            {item.description}
          </span>
          {item.amount !== undefined && (
            <span className="fontMono text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
              ${item.amount.toLocaleString()}
            </span>
          )}
        </div>
      ))}
    </div>
  )
);
ActivityFeed.displayName = "ActivityFeed";

export { ActivityFeed };
