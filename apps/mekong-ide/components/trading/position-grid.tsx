"use client";

/**
 * PositionGrid — responsive CSS grid of position cards.
 */

import { PositionCard } from "./position-card";
import type { Position, FairValue } from "@/lib/types/trading-types";

interface PositionGridProps {
  positions: Position[];
  fairValues: FairValue[];
}

export function PositionGrid({ positions, fairValues }: PositionGridProps) {
  const fvMap = new Map(fairValues.map((fv) => [fv.ticker, fv.edgePct]));

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
      gap: "0.75rem",
    }}>
      {positions.map((pos) => (
        <PositionCard
          key={pos.id}
          position={pos}
          fairValueEdgePct={fvMap.get(pos.ticker)}
        />
      ))}
    </div>
  );
}
