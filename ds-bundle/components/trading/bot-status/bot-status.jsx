// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/trading/bot-status.tsx
// Bundled in _ds_bundle.js as window.BotStatus

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface BotStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  strategy: string;
  status: "online" | "degraded" | "offline";
  uptime: string;
  lastAction: string;
}

const statusConfig = {
  online: { dot: "bg-[var(-ColorSuccess500)]", label: "Online" },
  degraded: { dot: "bg-[var(-ColorWarning500)]", label: "Degraded" },
  offline: { dot: "bg-[var(-ColorNeutral400)]", label: "Offline" },
};

const BotStatus = React.forwardRef<HTMLDivElement, BotStatusProps>(
  ({ className, name, strategy, status, uptime, lastAction, ...props }, ref) => {
    const config = statusConfig[status];
    return (
      <div
        className={cn(
          "flex itemsCenter gap-[var(-Spacing4)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing4)]",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="relative">
          <span className={cn("block h3 w3 roundedFull", config.dot)} />
          {status === "online" && (
            <span className={cn("absolute inset0 h3 w3 animatePing roundedFull opacity75", config.dot)} />
          )}
        </div>
        <div className="flex flex1 flexCol">
          <span className="text-[var(-FontSizeSm)] fontSemibold text-[var(-TextPrimary)]">{name}</span>
          <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">{strategy}</span>
        </div>
        <div className="flex flexCol itemsEnd">
          <span className="text-[var(-FontSizeXs)] text-[var(-TextSecondary)]">{uptime}</span>
          <span className="text-[var(-FontSizeXs)] text-[var(-TextTertiary)]">{lastAction}</span>
        </div>
      </div>
    );
  }
);
BotStatus.displayName = "BotStatus";

export { BotStatus };
