"use client";

/**
 * CashClawTradingScreen — Screen 8 (1440x900): 4-quadrant trading dashboard.
 * Top-left: positions, Top-right: fair value cache, Bottom-left: controls, Bottom-right: signal feed.
 */

import { Badge } from "@/components/ds";
import { PositionGrid } from "@/components/trading/position-grid";
import { FairValueCacheTable } from "@/components/trading/fair-value-cache-table";
import { TradingControls } from "@/components/trading/trading-controls";
import { LlmSignalFeed } from "@/components/trading/llm-signal-feed";
import {
  MOCK_POSITIONS,
  MOCK_FAIR_VALUES,
  MOCK_SIGNALS,
  MOCK_TRADING_STATS,
} from "@/lib/mock/trading-mock-data";

export function CashClawTradingScreen() {
  const stats = MOCK_TRADING_STATS;
  const isPnlPositive = stats.totalPnl >= 0;
  const pnlColor = isPnlPositive ? "var(--status-success)" : "var(--status-danger)";
  const pnlSign = isPnlPositive ? "+" : "";

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "var(--bg-primary)",
      fontFamily: "var(--font-mono, monospace)",
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "1rem",
        padding: "0.75rem 1.25rem",
        borderBottom: "1px solid var(--border-subtle)",
        background: "var(--bg-secondary)",
        flexShrink: 0,
      }}>
        <h1 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
          CashClaw
        </h1>
        <Badge variant={stats.mode === "paper" ? "warning" : "success"} label={stats.mode.toUpperCase()} dot />

        {/* Stats */}
        <div style={{ display: "flex", gap: "1.5rem", marginLeft: "1rem" }}>
          <div style={{ fontSize: "0.8125rem" }}>
            <span style={{ color: "var(--text-muted)" }}>P&L </span>
            <span style={{ color: pnlColor, fontWeight: 600 }}>
              {pnlSign}${stats.totalPnl.toLocaleString()} ({pnlSign}{stats.totalPnlPct.toFixed(2)}%)
            </span>
          </div>
          <div style={{ fontSize: "0.8125rem" }}>
            <span style={{ color: "var(--text-muted)" }}>Balance </span>
            <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>
              ${stats.balance.toLocaleString()}
            </span>
          </div>
          <div style={{ fontSize: "0.8125rem" }}>
            <span style={{ color: "var(--text-muted)" }}>Positions </span>
            <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{stats.openPositions}</span>
          </div>
        </div>
      </div>

      {/* Four-quadrant grid */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1.4fr", gridTemplateRows: "1fr 1fr", overflow: "hidden" }}>
        {/* Top-left: Positions */}
        <div style={{ borderRight: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)", overflow: "auto", padding: "0.875rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
            Open Positions
          </div>
          <PositionGrid positions={MOCK_POSITIONS} fairValues={MOCK_FAIR_VALUES} />
        </div>

        {/* Top-right: Fair Value Cache */}
        <div style={{ borderBottom: "1px solid var(--border-subtle)", overflow: "auto", padding: "0.875rem" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
            Fair Value Cache
          </div>
          <FairValueCacheTable fairValues={MOCK_FAIR_VALUES} />
        </div>

        {/* Bottom-left: Trading Controls */}
        <div style={{ borderRight: "1px solid var(--border-subtle)", overflow: "auto" }}>
          <div style={{ padding: "0.875rem 0.875rem 0", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Trading Controls
          </div>
          <TradingControls isPaperMode={stats.mode === "paper"} />
        </div>

        {/* Bottom-right: LLM Signal Feed */}
        <div style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <LlmSignalFeed signals={MOCK_SIGNALS} />
        </div>
      </div>
    </div>
  );
}
