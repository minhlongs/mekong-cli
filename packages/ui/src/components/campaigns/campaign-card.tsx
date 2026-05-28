"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const campaignStatus = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: { status: { active: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]", draft: "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]", paused: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]", ended: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]" } },
  defaultVariants: { status: "draft" },
});
export interface CampaignCardProps extends React.HTMLAttributes<HTMLDivElement> { name: string; status: "active" | "draft" | "paused" | "ended"; budget: number; roi: number; channels: string[]; }
const CampaignCard = React.forwardRef<HTMLDivElement, CampaignCardProps>(({ className, name, status, budget, roi, channels, ...props }, ref) => (
  <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="flex itemsCenter justifyBetween"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">{name}</span><span className={campaignStatus({ status })}>{status}</span></div>
    <div className="flex itemsCenter gap-[var(-SpacingLg)] text-[var(-FontXs)]"><span className="text-[var(-TextMuted)]">${budget.toLocaleString()}</span><span className={cn("fontMono", roi > 0 ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusError)]")}>{roi > 0 ? "+" : ""}{roi}% ROI</span></div>
    <div className="flex gap-[var(-SpacingXs)]">{channels.map((ch) => (<span key={ch} className="rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px1.5 py0.5 text-[var(-FontXs)] text-[var(-TextMuted)]">{ch}</span>))}</div>
  </div>
));
CampaignCard.displayName = "CampaignCard";
export { CampaignCard };
