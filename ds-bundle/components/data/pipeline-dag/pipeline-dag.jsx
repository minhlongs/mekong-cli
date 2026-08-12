// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/data/pipeline-dag.tsx
// Bundled in _ds_bundle.js as window.PipelineDag

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const nodeStatus = cva("flex h10 itemsCenter justifyCenter rounded-[var(-RadiusMd)] px-[var(-SpacingMd)] text-[var(-FontXs)] fontMedium border", {
  variants: {
    status: {
      running: "border-[var(-AccentTeal500)] bg-[var(-AccentTeal500)]/10 text-[var(-AccentTeal400)] animatePulse",
      success: "border-[var(-StatusHealthy)] bg-[var(-StatusHealthy)]/10 text-[var(-StatusHealthy)]",
      failed: "border-[var(-StatusError)] bg-[var(-StatusError)]/10 text-[var(-StatusError)]",
      pending: "border-[var(-BorderDefault)] bg-[var(-BgTertiary)] text-[var(-TextMuted)]",
    },
  },
  defaultVariants: { status: "pending" },
});

export interface DagNode { id: string; name: string; status: "running" | "success" | "failed" | "pending"; }
export interface PipelineDagProps extends React.HTMLAttributes<HTMLDivElement> {
  stages: DagNode[][];
}

const PipelineDag = React.forwardRef<HTMLDivElement, PipelineDagProps>(
  ({ className, stages, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Pipeline DAG</div>
      <div className="flex itemsCenter gap-[var(-SpacingSm)]">
        {stages.map((stage, si) => (
          <React.Fragment key={si}>
            <div className="flex flexCol gap-[var(-SpacingXs)]">
              {stage.map((node) => (
                <div key={node.id} className={nodeStatus({ status: node.status })}>{node.name}</div>
              ))}
            </div>
            {si < stages.length - 1 && <div className="h0.5 w6 bg-[var(-BorderDefault)]" />}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
);
PipelineDag.displayName = "PipelineDag";
export { PipelineDag };
