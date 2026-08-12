// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/security/threat-feed.tsx
// Bundled in _ds_bundle.js as window.ThreatFeed

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const severityDot = cva("inlineBlock h2 w2 roundedFull", {
  variants: {
    severity: {
      critical: "bg-[var(-StatusError)]",
      high: "bg-[var(-StatusWarning)]",
      medium: "bg-[var(-AccentTeal400)]",
      low: "bg-[var(-StatusIdle)]",
      info: "bg-[var(-ModelQwen)]",
    },
  },
  defaultVariants: { severity: "info" },
});

export interface ThreatEvent {
  time: string;
  type: string;
  source: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
}

export interface ThreatFeedProps extends React.HTMLAttributes<HTMLDivElement> {
  events: ThreatEvent[];
}

const ThreatFeed = React.forwardRef<HTMLDivElement, ThreatFeedProps>(
  ({ className, events, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flexCol rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden",
        className
      )}
      {...props}
    >
      <div className="borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]">
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">
          Threat Feed
        </span>
      </div>
      <div className="flex maxH80 flexCol overflowYAuto">
        {events.map((event, i) => (
          <div
            key={i}
            className="flex itemsCenter gap-[var(-SpacingMd)] borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0 hover:bg-[var(-SurfaceHover)]"
          >
            <span className={severityDot({ severity: event.severity })} />
            <span className="minW-[60px] fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">
              {event.time}
            </span>
            <span className="flex1 text-[var(-FontSm)] text-[var(-TextPrimary)]">
              {event.type}
            </span>
            <span className="text-[var(-FontXs)] text-[var(-TextSecondary)]">
              {event.source}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
);
ThreatFeed.displayName = "ThreatFeed";

export { ThreatFeed };
