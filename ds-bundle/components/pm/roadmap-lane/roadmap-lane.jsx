// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pm/roadmap-lane.tsx
// Bundled in _ds_bundle.js as window.RoadmapLane

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const laneBg = cva("rounded-[var(-RadiusLg)] border p-[var(-SpacingLg)]", {
  variants: {
    lane: {
      now: "border-[var(-StatusHealthy)]/30 bg-[var(-StatusHealthy)]/5",
      next: "border-[var(-StatusWarning)]/30 bg-[var(-StatusWarning)]/5",
      later: "border-[var(-BorderDefault)] bg-[var(-SurfaceCard)]",
    },
  },
  defaultVariants: { lane: "later" },
});

export interface RoadmapItem { title: string; score: number; tag: string; }
export interface RoadmapLaneProps extends React.HTMLAttributes<HTMLDivElement> {
  lane: "now" | "next" | "later";
  items: RoadmapItem[];
}

const RoadmapLane = React.forwardRef<HTMLDivElement, RoadmapLaneProps>(
  ({ className, lane, items, ...props }, ref) => (
    <div ref={ref} className={cn(laneBg({ lane }), className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontBold uppercase trackingWider text-[var(-TextSecondary)]">{lane}</div>
      <div className="flex flexCol gap-[var(-SpacingSm)]">
        {items.map((item, i) => (
          <div key={i} className="flex itemsCenter justifyBetween rounded-[var(-RadiusMd)] bg-[var(-BgPrimary)]/50 px-[var(-SpacingMd)] py-[var(-SpacingSm)]">
            <span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">{item.title}</span>
            <div className="flex itemsCenter gap-[var(-SpacingSm)]">
              <span className="rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px1.5 py0.5 text-[var(-FontXs)] text-[var(-TextMuted)]">{item.tag}</span>
              <span className="fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)]">{item.score}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
);
RoadmapLane.displayName = "RoadmapLane";
export { RoadmapLane };
