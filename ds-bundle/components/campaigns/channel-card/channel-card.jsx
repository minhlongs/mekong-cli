// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/campaigns/channel-card.tsx
// Bundled in _ds_bundle.js as window.ChannelCard

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ChannelCardProps extends React.HTMLAttributes<HTMLDivElement> { channel: string; visitors: number; conversions: number; trend: "up" | "down" | "flat"; }
const ChannelCard = React.forwardRef<HTMLDivElement, ChannelCardProps>(({ className, channel, visitors, conversions, trend, ...props }, ref) => (
  <div ref={ref} className={cn("flex itemsCenter justifyBetween rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] px-[var(-SpacingLg)] py-[var(-SpacingMd)]", className)} {...props}>
    <span className="text-[var(-FontSm)] fontMedium text-[var(-TextPrimary)]">{channel}</span>
    <div className="flex itemsCenter gap-[var(-SpacingLg)] text-[var(-FontXs)]"><span className="fontMono text-[var(-TextSecondary)]">{visitors.toLocaleString()} visits</span><span className="fontMono text-[var(-TextSecondary)]">{conversions} conv</span><span className={cn("fontBold", trend === "up" ? "text-[var(-StatusHealthy)]" : trend === "down" ? "text-[var(-StatusError)]" : "text-[var(-TextMuted)]")}>{trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"}</span></div>
  </div>
));
ChannelCard.displayName = "ChannelCard";
export { ChannelCard };
