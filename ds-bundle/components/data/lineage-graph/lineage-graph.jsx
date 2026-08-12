// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/data/lineage-graph.tsx
// Bundled in _ds_bundle.js as window.LineageGraph

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface LineageNode { id: string; name: string; type: "source" | "transform" | "target"; }
export interface LineageEdge { from: string; to: string; }
export interface LineageGraphProps extends React.HTMLAttributes<HTMLDivElement> {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

const typeColor = { source: "var(-ModelGemma)", transform: "var(-ModelDeepseek)", target: "var(-AccentTeal500)" };

const LineageGraph = React.forwardRef<HTMLDivElement, LineageGraphProps>(
  ({ className, nodes, edges, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Data Lineage</div>
      <div className="flex flexWrap gap-[var(-SpacingMd)]">
        {nodes.map((node) => (
          <div key={node.id} className="flex itemsCenter gap-[var(-SpacingXs)] rounded-[var(-RadiusMd)] border border-[var(-BorderDefault)] bg-[var(-BgTertiary)] px-[var(-SpacingMd)] py-[var(-SpacingSm)]">
            <span className="h2 w2 roundedFull" style={{ backgroundColor: typeColor[node.type] }} />
            <span className="text-[var(-FontXs)] text-[var(-TextPrimary)]">{node.name}</span>
          </div>
        ))}
      </div>
      <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{edges.length} connections</div>
    </div>
  )
);
LineageGraph.displayName = "LineageGraph";
export { LineageGraph };
