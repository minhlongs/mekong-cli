// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/ml/cost-tracker.tsx
// Bundled in _ds_bundle.js as window.CostTracker

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface ModelCost { model: string; requests: number; cost: number; color: string; }
export interface CostTrackerProps extends React.HTMLAttributes<HTMLDivElement> { models: ModelCost[]; budget: number; }

const CostTracker = React.forwardRef<HTMLDivElement, CostTrackerProps>(
  ({ className, models, budget, ...props }, ref) => {
    const totalCost = models.reduce((sum, m) => sum + m.cost, 0);
    const pct = Math.round((totalCost / budget) * 100);
    return (
      <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
        <div className="flex itemsCenter justifyBetween mb-[var(-SpacingMd)]">
          <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Inference Cost</span>
          <span className={cn("fontMono text-[var(-FontSm)]", pct > 90 ? "text-[var(-StatusError)]" : "text-[var(-TextSecondary)]")}>${totalCost.toFixed(2)} / ${budget}</span>
        </div>
        <div className="h3 wFull overflowHidden roundedFull bg-[var(-BgTertiary)] mb-[var(-SpacingMd)]">
          <div className={cn("hFull roundedFull transitionAll", pct > 90 ? "bg-[var(-StatusError)]" : pct > 70 ? "bg-[var(-StatusWarning)]" : "bg-[var(-AccentTeal500)]")} style={{ width: `${Math.min(pct, 100)}%` }} />
        </div>
        <div className="flex flexCol gap-[var(-SpacingXs)]">
          {models.map((m, i) => (
            <div key={i} className="flex itemsCenter justifyBetween text-[var(-FontXs)]">
              <div className="flex itemsCenter gap-[var(-SpacingSm)]">
                <span className="h2 w2 roundedFull" style={{ backgroundColor: m.color }} />
                <span className="text-[var(-TextPrimary)]">{m.model}</span>
              </div>
              <div className="flex itemsCenter gap-[var(-SpacingLg)]">
                <span className="text-[var(-TextMuted)]">{m.requests.toLocaleString()} req</span>
                <span className="fontMono text-[var(-TextSecondary)]">${m.cost.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
);
CostTracker.displayName = "CostTracker";
export { CostTracker };
