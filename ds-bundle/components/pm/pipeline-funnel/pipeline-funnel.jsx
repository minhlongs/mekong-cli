// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pm/pipeline-funnel.tsx
// Bundled in _ds_bundle.js as window.PipelineFunnel

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface FunnelStage { name: string; value: number; count: number; }
export interface PipelineFunnelProps extends React.HTMLAttributes<HTMLDivElement> { stages: FunnelStage[]; }

const PipelineFunnel = React.forwardRef<HTMLDivElement, PipelineFunnelProps>(
  ({ className, stages, ...props }, ref) => {
    const max = Math.max(...stages.map((s) => s.value), 1);
    return (
      <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
        <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Revenue Funnel</div>
        <div className="flex flexCol gap-[var(-SpacingSm)]">
          {stages.map((stage, i) => {
            const width = Math.round((stage.value / max) * 100);
            return (
              <div key={i} className="flex itemsCenter gap-[var(-SpacingMd)]">
                <span className="w20 text-[var(-FontXs)] text-[var(-TextSecondary)] textRight">{stage.name}</span>
                <div className="flex1 h6 rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] overflowHidden">
                  <div className="hFull rounded-[var(-RadiusSm)] bg-[var(-AccentTeal500)]/60 flex itemsCenter px2 transitionAll" style={{ width: `${width}%` }}>
                    <span className="fontMono text-[var(-FontXs)] text-[var(-TextPrimary)]">${(stage.value / 1000).toFixed(0)}K</span>
                  </div>
                </div>
                <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w8 textRight">{stage.count}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
);
PipelineFunnel.displayName = "PipelineFunnel";
export { PipelineFunnel };
