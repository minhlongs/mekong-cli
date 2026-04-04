"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface EntityNode { name: string; type: "parent" | "subsidiary" | "branch"; jurisdiction: string; children?: EntityNode[]; }
export interface EntityTreeProps extends React.HTMLAttributes<HTMLDivElement> { root: EntityNode; }

function EntityItem({ node, depth = 0 }: { node: EntityNode; depth?: number }) {
  const typeColor = { parent: "var(--accent-teal-500)", subsidiary: "var(--model-gemma)", branch: "var(--model-qwen)" };
  return (
    <div style={{ paddingLeft: `${depth * 20}px` }}>
      <div className="flex items-center gap-[var(--spacing-sm)] py-[var(--spacing-xs)]">
        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: typeColor[node.type] }} />
        <span className="text-[var(--font-sm)] text-[var(--text-primary)]">{node.name}</span>
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">({node.jurisdiction})</span>
      </div>
      {node.children?.map((child, i) => <EntityItem key={i} node={child} depth={depth + 1} />)}
    </div>
  );
}

const EntityTree = React.forwardRef<HTMLDivElement, EntityTreeProps>(
  ({ className, root, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Corporate Structure</div>
      <EntityItem node={root} />
    </div>
  )
);
EntityTree.displayName = "EntityTree";
export { EntityTree };
