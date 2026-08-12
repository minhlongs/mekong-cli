// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pm/experiment-card.tsx
// Bundled in _ds_bundle.js as window.ExperimentCard

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const resultBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    result: {
      winning: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
      losing: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      inconclusive: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      running: "bg-[var(-ModelQwen)]/15 text-[var(-ModelQwen)]",
    },
  },
  defaultVariants: { result: "running" },
});

export interface ExperimentCardProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  hypothesis: string;
  variant: string;
  confidence: number;
  result: "winning" | "losing" | "inconclusive" | "running";
  sampleSize: number;
}

const ExperimentCard = React.forwardRef<HTMLDivElement, ExperimentCardProps>(
  ({ className, name, hypothesis, variant, confidence, result, sampleSize, ...props }, ref) => (
    <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="flex itemsCenter justifyBetween">
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">{name}</span>
        <span className={resultBadge({ result })}>{result}</span>
      </div>
      <p className="text-[var(-FontXs)] text-[var(-TextSecondary)]">{hypothesis}</p>
      <div className="flex itemsCenter gap-[var(-SpacingLg)] borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)] text-[var(-FontXs)]">
        <span className="text-[var(-TextMuted)]">Variant: {variant}</span>
        <span className="text-[var(-TextMuted)]">n={sampleSize.toLocaleString()}</span>
        <span className="fontMono text-[var(-AccentTeal400)]">{confidence}% confidence</span>
      </div>
    </div>
  )
);
ExperimentCard.displayName = "ExperimentCard";
export { ExperimentCard };
