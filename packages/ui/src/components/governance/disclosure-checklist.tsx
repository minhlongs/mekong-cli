"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface DisclosureItem { requirement: string; status: "complete" | "inProgress" | "notStarted"; deadline: string; }
export interface DisclosureChecklistProps extends React.HTMLAttributes<HTMLDivElement> { items: DisclosureItem[]; }

const statusIcon = { complete: "\u2713", "inProgress": "\u25CB", "notStarted": "\u2014" };
const statusClass = { complete: "text-[var(-StatusHealthy)]", "inProgress": "text-[var(-StatusWarning)]", "notStarted": "text-[var(-TextMuted)]" };

const DisclosureChecklist = React.forwardRef<HTMLDivElement, DisclosureChecklistProps>(
  ({ className, items, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className)} {...props}>
      <div className="borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]">
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">SEC Disclosure Checklist</span>
      </div>
      {items.map((item, i) => (
        <div key={i} className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingMd)] last:borderB0 hover:bg-[var(-SurfaceHover)]">
          <div className="flex itemsCenter gap-[var(-SpacingMd)]">
            <span className={cn("fontBold", statusClass[item.status])}>{statusIcon[item.status]}</span>
            <span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">{item.requirement}</span>
          </div>
          <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{item.deadline}</span>
        </div>
      ))}
    </div>
  )
);
DisclosureChecklist.displayName = "DisclosureChecklist";
export { DisclosureChecklist };
