// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/governance/entity-tree.tsx
// Bundled in _ds_bundle.js as window.EntityTree

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface EntityNode { name: string; type: "parent" | "subsidiary" | "branch"; jurisdiction: string; children?: EntityNode[]; }
export interface EntityTreeProps extends React.HTMLAttributes<HTMLDivElement> { root: EntityNode; }

function EntityItem({ node, depth = 0 }: { node: EntityNode; depth?: number }) {
  const typeColor = { parent: "var(-AccentTeal500)", subsidiary: "var(-ModelGemma)", branch: "var(-ModelQwen)" };
  return (
    <div style={{ paddingLeft: `${depth * 20}px` }}>
      <div className="flex itemsCenter gap-[var(-SpacingSm)] py-[var(-SpacingXs)]">
        <span className="h2 w2 roundedFull" style={{ backgroundColor: typeColor[node.type] }} />
        <span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">{node.name}</span>
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">({node.jurisdiction})</span>
      </div>
      {node.children?.map((child, i) => <EntityItem key={i} node={child} depth={depth + 1} />)}
    </div>
  );
}

const EntityTree = React.forwardRef<HTMLDivElement, EntityTreeProps>(
  ({ className, root, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Corporate Structure</div>
      <EntityItem node={root} />
    </div>
  )
);
EntityTree.displayName = "EntityTree";
export { EntityTree };
