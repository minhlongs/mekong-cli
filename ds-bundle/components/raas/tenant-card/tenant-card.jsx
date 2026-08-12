// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/raas/tenant-card.tsx
// Bundled in _ds_bundle.js as window.TenantCard

"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const tierBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: { tier: { starter: "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]", pro: "bg-[var(-AccentTeal500)]/15 text-[var(-AccentTeal400)]", enterprise: "bg-[var(-Primary)]/15 text-[var(-Primary)]" } },
  defaultVariants: { tier: "starter" },
});
export interface TenantCardProps extends React.HTMLAttributes<HTMLDivElement> { name: string; tier: "starter" | "pro" | "enterprise"; health: number; usage: number; apiCalls: number; }
const TenantCard = React.forwardRef<HTMLDivElement, TenantCardProps>(({ className, name, tier, health, usage, apiCalls, ...props }, ref) => (
  <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="flex itemsCenter justifyBetween"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">{name}</span><span className={tierBadge({ tier })}>{tier}</span></div>
    <div className="grid gridCols3 gap-[var(-SpacingSm)] text-[var(-FontXs)]">
      <div className="flex flexCol"><span className="text-[var(-TextMuted)]">Health</span><span className={cn("fontMono", health > 90 ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]")}>{health}%</span></div>
      <div className="flex flexCol"><span className="text-[var(-TextMuted)]">Usage</span><span className="fontMono text-[var(-TextPrimary)]">{usage}%</span></div>
      <div className="flex flexCol"><span className="text-[var(-TextMuted)]">API Calls</span><span className="fontMono text-[var(-TextPrimary)]">{apiCalls.toLocaleString()}</span></div>
    </div>
  </div>
));
TenantCard.displayName = "TenantCard";
export { TenantCard };
