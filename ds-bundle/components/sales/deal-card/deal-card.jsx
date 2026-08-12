// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/sales/deal-card.tsx
// Bundled in _ds_bundle.js as window.DealCard

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface DealCardProps extends React.HTMLAttributes<HTMLDivElement> { company: string; value: number; stage: string; probability: number; owner: string; }
const DealCard = React.forwardRef<HTMLDivElement, DealCardProps>(({ className, company, value, stage, probability, owner, ...props }, ref) => (
  <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="flex itemsCenter justifyBetween"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">{company}</span><span className="fontMono text-[var(-FontSm)] text-[var(-AccentTeal400)]">${(value / 1000).toFixed(0)}K</span></div>
    <div className="flex itemsCenter justifyBetween text-[var(-FontXs)]"><span className="rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px1.5 py0.5 text-[var(-TextMuted)]">{stage}</span><span className="text-[var(-TextSecondary)]">{probability}%</span><span className="text-[var(-TextMuted)]">{owner}</span></div>
  </div>
));
DealCard.displayName = "DealCard";
export { DealCard };
