// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/dashboard/mission-card.tsx
// Bundled in _ds_bundle.js as window.MissionCard

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MissionCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  status: "pending" | "running" | "success" | "failed";
  creditCost: number;
  agents?: string[];
  expandable?: boolean;
}

const statusStyles: Record<string, string> = {
  pending: "bg-[var(-BgTertiary)] text-[var(-TextSecondary)]",
  running: "bg-[var(-ColorInfo500)]/15 text-[var(-ColorInfo500)]",
  success: "bg-[var(-ColorSuccess500)]/15 text-[var(-ColorSuccess500)]",
  failed: "bg-[var(-ColorDanger500)]/15 text-[var(-ColorDanger500)]",
};

const MissionCard = React.forwardRef<HTMLDivElement, MissionCardProps>(
  ({ className, title, status, creditCost, agents = [], expandable, children, ...props }, ref) => {
    const [expanded, setExpanded] = React.useState(false);

    return (
      <div
        className={cn(
          "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] transitionShadow duration-[var(-DurationNormal)]",
          status === "running" && "ring1 ring-[var(-ColorInfo500)]/30",
          className
        )}
        ref={ref}
        {...props}
      >
        <div
          className={cn("flex itemsCenter gap3 p-[var(-Spacing4)]", expandable && "cursorPointer")}
          onClick={expandable ? () => setExpanded(!expanded) : undefined}
        >
          <div className="flex flex1 flexCol gap1">
            <span className="text-[var(-FontSizeSm)] fontMedium text-[var(-TextPrimary)]">{title}</span>
            <div className="flex itemsCenter gap2">
              <span className={cn(
                "rounded-[var(-RadiusFull)] px2 py0.5 text-[0.625rem] fontSemibold uppercase",
                statusStyles[status]
              )}>
                {status}
              </span>
              <span className="fontMono text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">
                {creditCost} MCU
              </span>
            </div>
          </div>
          {agents.length > 0 && (
            <div className="flex SpaceX1">
              {agents.map((agent) => (
                <span
                  key={agent}
                  className="flex h6 w6 itemsCenter justifyCenter roundedFull bg-[var(-Accent)] text-[0.625rem] fontBold text-[var(-AccentText)]"
                  title={agent}
                >
                  {agent[0]}
                </span>
              ))}
            </div>
          )}
          {expandable && (
            <span className={cn(
              "text-[var(-TextTertiary)] transitionTransform duration-[var(-DurationFast)]",
              expanded && "rotate180"
            )}>
              &#x25BC;
            </span>
          )}
        </div>
        {expandable && expanded && children && (
          <div className="borderT border-[var(-BorderDefault)] p-[var(-Spacing4)]">
            {children}
          </div>
        )}
      </div>