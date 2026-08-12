// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/ml/model-card.tsx
// Bundled in _ds_bundle.js as window.ModelCard

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const modelStatusBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    status: {
      serving: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
      canary: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      shadow: "bg-[var(-ModelDeepseek)]/15 text-[var(-ModelDeepseek)]",
      retired: "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]",
    },
  },
  defaultVariants: { status: "serving" },
});

export interface ModelCardProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  version: string;
  status: "serving" | "canary" | "shadow" | "retired";
  latencyP99: number;
  costPer1k: number;
  driftScore: number;
}

const ModelCard = React.forwardRef<HTMLDivElement, ModelCardProps>(
  ({ className, name, version, status, latencyP99, costPer1k, driftScore, ...props }, ref) => (
    <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="flex itemsCenter justifyBetween">
        <div className="flex itemsCenter gap-[var(-SpacingSm)]">
          <span className="text-[var(-FontMd)] fontSemibold text-[var(-TextPrimary)]">{name}</span>
          <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">v{version}</span>
        </div>
        <span className={modelStatusBadge({ status })}>{status}</span>
      </div>
      <div className="grid gridCols3 gap-[var(-SpacingMd)] borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]">
        <div className="flex flexCol">
          <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">P99 Latency</span>
          <span className="fontMono text-[var(-FontSm)] text-[var(-TextPrimary)]">{latencyP99}ms</span>
        </div>
        <div className="flex flexCol">
          <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Cost/1K</span>
          <span className="fontMono text-[var(-FontSm)] text-[var(-TextPrimary)]">${costPer1k.toFixed(3)}</span>
        </div>
        <div className="flex flexCol">
          <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Drift</span>
          <span className={cn("fontMono text-[var(-FontSm)]", driftScore > 0.1 ? "text-[var(-StatusError)]" : "text-[var(-StatusHealthy)]")}>{driftScore.toFixed(3)}</span>
        </div>
      </div>
    </div>
  )
);
ModelCard.displayName = "ModelCard";
export { ModelCard };
