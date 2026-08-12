// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pm/feature-flag.tsx
// Bundled in _ds_bundle.js as window.FeatureFlag

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface FeatureFlagProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  enabled: boolean;
  rolloutPct: number;
  environment: "production" | "staging" | "development";
}

const FeatureFlag = React.forwardRef<HTMLDivElement, FeatureFlagProps>(
  ({ className, name, enabled, rolloutPct, environment, ...props }, ref) => (
    <div ref={ref} className={cn("flex itemsCenter justifyBetween rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] px-[var(-SpacingLg)] py-[var(-SpacingMd)]", className)} {...props}>
      <div className="flex itemsCenter gap-[var(-SpacingMd)]">
        <div className={cn("h3 w3 roundedFull", enabled ? "bg-[var(-StatusHealthy)]" : "bg-[var(-StatusIdle)]")} />
        <span className="fontMono text-[var(-FontSm)] text-[var(-TextPrimary)]">{name}</span>
      </div>
      <div className="flex itemsCenter gap-[var(-SpacingLg)]">
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{environment}</span>
        <div className="flex itemsCenter gap-[var(-SpacingSm)]">
          <div className="h1.5 w20 overflowHidden roundedFull bg-[var(-BgTertiary)]">
            <div className="hFull roundedFull bg-[var(-AccentTeal500)]" style={{ width: `${rolloutPct}%` }} />
          </div>
          <span className="fontMono text-[var(-FontXs)] text-[var(-TextSecondary)]">{rolloutPct}%</span>
        </div>
      </div>
    </div>
  )
);
FeatureFlag.displayName = "FeatureFlag";
export { FeatureFlag };
