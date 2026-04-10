"use client";

/**
 * PositionCard — displays a single trading position: ticker, side, entry/current, PnL, fair value bar.
 */

import { Card, Badge } from "@/components/ds";
import type { Position } from "@/lib/types/trading-types";

interface PositionCardProps {
  position: Position;
  fairValueEdgePct?: number;
}

export function PositionCard({ position, fairValueEdgePct }: PositionCardProps) {
  const isPnlPositive = position.unrealizedPnl >= 0;
  const pnlColor = isPnlPositive ? "var(--status-success)" : "var(--status-danger)";
  const pnlSign = isPnlPositive ? "+" : "";

  // Fair value bar: clamp edge to -20%..+20% for visual
  const clampedEdge = Math.max(-20, Math.min(20, fairValueEdgePct ?? 0));
  const barWidth = Math.abs(clampedEdge) / 20 * 100;
  const barColor = (fairValueEdgePct ?? 0) >= 0 ? "var(--status-success)" : "var(--status-danger)";

  return (
    <Card>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {/* Ticker + side */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {position.ticker}
          </span>
          <Badge
            variant={position.side === "long" ? "success" : "danger"}
            label={position.side.toUpperCase()}
          />
        </div>

        {/* PnL */}
        <div style={{ fontSize: "1.25rem", fontWeight: 700, color: pnlColor }}>
          {pnlSign}{position.unrealizedPnl.toFixed(2)}
          <span style={{ fontSize: "0.75rem", fontWeight: 400, marginLeft: "0.25rem" }}>
            ({pnlSign}{position.unrealizedPnlPct.toFixed(2)}%)
          </span>
        </div>

        {/* Price info */}
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
          <div style={{ color: "var(--text-muted)" }}>
            Entry <span style={{ color: "var(--text-secondary)" }}>${position.entryPrice.toFixed(2)}</span>
          </div>
          <div style={{ color: "var(--text-muted)" }}>
            Now <span style={{ color: "var(--text-primary)" }}>${position.currentPrice.toFixed(2)}</span>
          </div>
          <div style={{ color: "var(--text-muted)" }}>
            Size <span style={{ color: "var(--text-secondary)" }}>{position.size}</span>
          </div>
        </div>

        {/* Fair value bar */}
        {fairValueEdgePct !== undefined && (
          <div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
              FV edge: {fairValueEdgePct >= 0 ? "+" : ""}{fairValueEdgePct.toFixed(1)}%
            </div>
            <div style={{ height: "4px", background: "var(--border-subtle)", borderRadius: "2px", overflow: "hidden" }}>
              <div style={{ width: `${barWidth}%`, height: "100%", background: barColor, borderRadius: "2px", transition: "width 0.3s" }} />
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
