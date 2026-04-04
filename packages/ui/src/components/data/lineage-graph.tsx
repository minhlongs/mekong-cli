"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface LineageNode { id: string; name: string; type: "source" | "transform" | "target"; }
export interface LineageEdge { from: string; to: string; }
export interface LineageGraphProps extends React.HTMLAttributes<HTMLDivElement> {
  nodes: LineageNode[];
  edges: LineageEdge[];
}

const typeColor = { source: "var(--model-gemma)", transform: "var(--model-deepseek)", target: "var(--accent-teal-500)" };

const LineageGraph = React.forwardRef<HTMLDivElement, LineageGraphProps>(
  ({ className, nodes, edges, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Data Lineage</div>
      <div className="flex flex-wrap gap-[var(--spacing-md)]">
        {nodes.map((node) => (
          <div key={node.id} className="flex items-center gap-[var(--spacing-xs)] rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-tertiary)] px-[var(--spacing-md)] py-[var(--spacing-sm)]">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: typeColor[node.type] }} />
            <span className="text-[var(--font-xs)] text-[var(--text-primary)]">{node.name}</span>
          </div>
        ))}
      </div>
      <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-muted)]">{edges.length} connections</div>
    </div>
  )
);
LineageGraph.displayName = "LineageGraph";
export { LineageGraph };
