// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/ipo/readiness-score.tsx
// Bundled in _ds_bundle.js as window.ReadinessScore

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ReadinessCategory { name: string; score: number; weight: number; }
export interface ReadinessScoreProps extends React.HTMLAttributes<HTMLDivElement> { overall: number; categories: ReadinessCategory[]; target: number; }
const ReadinessScore = React.forwardRef<HTMLDivElement, ReadinessScoreProps>(({ className, overall, categories, target, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="flex itemsCenter justifyBetween mb-[var(-SpacingMd)]"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">IPO Readiness</span><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Target: {target}%</span></div>
    <div className={cn("fontMono text-[var(-Font3xl)] fontBold", overall >= target ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]")}>{overall}%</div>
    <div className="mt-[var(-SpacingMd)] flex flexCol gap-[var(-SpacingXs)]">
      {categories.map((c, i) => (<div key={i} className="flex itemsCenter gap-[var(-SpacingSm)]"><span className="w24 text-[var(-FontXs)] text-[var(-TextSecondary)]">{c.name}</span><div className="flex1 h1.5 roundedFull bg-[var(-BgTertiary)] overflowHidden"><div className="hFull roundedFull bg-[var(-AccentTeal500)]" style={{ width: `${c.score}%` }} /></div><span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)] w8 textRight">{c.score}%</span></div>))}
    </div>
  </div>
));
ReadinessScore.displayName = "ReadinessScore";
export { ReadinessScore };
