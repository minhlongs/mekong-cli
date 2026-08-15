"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface PipelineStageProps extends React.HTMLAttributes<HTMLDivElement> { stage: string; count: number; value: number; }
const PipelineStage = React.forwardRef<HTMLDivElement, PipelineStageProps>(({ className, stage, count, value, ...props }, ref) => (
  <div ref={ref} className={cn("flex flexCol itemsCenter gap-[var(-SpacingXs)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingMd)]", className)} {...props}>
    <span className="text-[var(-FontXs)] text-[var(-TextMuted)] uppercase trackingWider">{stage}</span>
    <span className="fontMono text-[var(-FontXl)] fontBold text-[var(-TextPrimary)]">{count}</span>
    <span className="fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)]">${(value / 1000).toFixed(0)}K</span>
  </div>
));
PipelineStage.displayName = "PipelineStage";
export { PipelineStage };
