// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/audit/sox-progress.tsx
// Bundled in _ds_bundle.js as window.SoxProgress

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface SoxProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  phases: { name: string; total: number; completed: number }[];
}

const SoxProgress = React.forwardRef<HTMLDivElement, SoxProgressProps>(
  ({ className, phases, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">SOX ICFR Progress</div>
      <div className="flex flexCol gap-[var(-SpacingMd)]">
        {phases.map((phase, i) => {
          const pct = phase.total > 0 ? Math.round((phase.completed / phase.total) * 100) : 0;
          return (
            <div key={i} className="flex flexCol gap-[var(-SpacingXs)]">
              <div className="flex itemsCenter justifyBetween">
                <span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">{phase.name}</span>
                <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">{phase.completed}/{phase.total}</span>
              </div>
              <div className="h2 wFull overflowHidden roundedFull bg-[var(-BgTertiary)]">
                <div className="hFull roundedFull bg-[var(-AccentTeal500)] transitionAll duration500" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  )
);
SoxProgress.displayName = "SoxProgress";
export { SoxProgress };
