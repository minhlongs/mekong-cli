// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/data/metric-definition.tsx
// Bundled in _ds_bundle.js as window.MetricDefinition

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MetricDefinitionProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  definition: string;
  formula: string;
  owner: string;
  lastUpdated: string;
}

const MetricDefinition = React.forwardRef<HTMLDivElement, MetricDefinitionProps>(
  ({ className, name, definition, formula, owner, lastUpdated, ...props }, ref) => (
    <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <span className="text-[var(-FontMd)] fontSemibold text-[var(-TextPrimary)]">{name}</span>
      <p className="text-[var(-FontSm)] text-[var(-TextSecondary)]">{definition}</p>
      <code className="rounded-[var(-RadiusSm)] bg-[var(-BgTertiary)] px-[var(-SpacingSm)] py-[var(-SpacingXs)] fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)]">{formula}</code>
      <div className="flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]">
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Owner: {owner}</span>
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{lastUpdated}</span>
      </div>
    </div>
  )
);
MetricDefinition.displayName = "MetricDefinition";
export { MetricDefinition };
