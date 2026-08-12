// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/data/quality-score.tsx
// Bundled in _ds_bundle.js as window.QualityScore

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface QualityDimension { name: string; score: number; status: "pass" | "warn" | "fail"; }
export interface QualityScoreProps extends React.HTMLAttributes<HTMLDivElement> {
  dimensions: QualityDimension[];
}

const statusColor = { pass: "var(-StatusHealthy)", warn: "var(-StatusWarning)", fail: "var(-StatusError)" };

const QualityScore = React.forwardRef<HTMLDivElement, QualityScoreProps>(
  ({ className, dimensions, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Data Quality</div>
      <div className="flex flexCol gap-[var(-SpacingMd)]">
        {dimensions.map((d, i) => (
          <div key={i} className="flex itemsCenter gap-[var(-SpacingMd)]">
            <span className="w24 text-[var(-FontSm)] text-[var(-TextSecondary)]">{d.name}</span>
            <div className="flex1 h2 roundedFull bg-[var(-BgTertiary)] overflowHidden">
              <div className="hFull roundedFull transitionAll" style={{ width: `${d.score}%`, backgroundColor: statusColor[d.status] }} />
            </div>
            <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w10 textRight">{d.score}%</span>
          </div>
        ))}
      </div>
    </div>
  )
);
QualityScore.displayName = "QualityScore";
export { QualityScore };
