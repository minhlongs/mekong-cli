"use client";

/**
 * TradingControls — manual trade form: market select, side, size, buy/sell/close buttons.
 */

import { useState } from "react";
import { Button, Input } from "@/components/ds";
import type { TradeSide } from "@/lib/types/trading-types";

const TICKERS = ["AAPL", "NVDA", "TSLA", "MSFT", "SPY", "AMZN", "GOOGL", "META", "BTC", "ETH"];

interface TradingControlsProps {
  isPaperMode?: boolean;
}

export function TradingControls({ isPaperMode = true }: TradingControlsProps) {
  const [ticker, setTicker] = useState("AAPL");
  const [side, setSide] = useState<TradeSide>("long");
  const [size, setSize] = useState("10");
  const [submitted, setSubmitted] = useState<string | null>(null);

  function handleSubmit(action: "open" | "close") {
    if (!size || isNaN(Number(size)) || Number(size) <= 0) return;
    const msg = action === "open"
      ? `${isPaperMode ? "[Paper] " : ""}${side.toUpperCase()} ${size}x ${ticker}`
      : `[Close] ${ticker}`;
    setSubmitted(msg);
    setTimeout(() => setSubmitted(null), 2000);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", padding: "0.875rem" }}>
      {/* Ticker select */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 500 }}>Market</label>
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          style={{
            padding: "0.5rem 0.75rem",
            fontSize: "0.875rem",
            background: "var(--surface-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-strong)",
            borderRadius: "0.375rem",
            cursor: "pointer",
          }}
        >
          {TICKERS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Side toggle */}
      <div>
        <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 500, display: "block", marginBottom: "0.25rem" }}>Side</label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {(["long", "short"] as TradeSide[]).map((s) => (
            <button
              key={s}
              onClick={() => setSide(s)}
              style={{
                flex: 1,
                padding: "0.375rem",
                fontSize: "0.8125rem",
                fontWeight: 600,
                borderRadius: "0.375rem",
                cursor: "pointer",
                border: "none",
                background: side === s
                  ? (s === "long" ? "var(--status-success)" : "var(--status-danger)")
                  : "var(--surface-card)",
                color: side === s ? "#fff" : "var(--text-secondary)",
                transition: "background 0.15s",
              }}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Size input */}
      <Input
        label="Size (units)"
        type="number"
        min="1"
        value={size}
        onChange={(e) => setSize(e.target.value)}
        placeholder="10"
      />

      {/* Action buttons */}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <Button variant="primary" size="sm" style={{ flex: 1 }} onClick={() => handleSubmit("open")}>
          {side === "long" ? "Buy" : "Sell"}
        </Button>
        <Button variant="secondary" size="sm" onClick={() => handleSubmit("close")}>
          Close
        </Button>
      </div>

      {/* Confirmation flash */}
      {submitted && (
        <div style={{
          padding: "0.5rem 0.75rem",
          background: "rgba(34,197,94,0.15)",
          border: "1px solid var(--status-success)",
          borderRadius: "0.375rem",
          fontSize: "0.8125rem",
          color: "var(--status-success)",
        }}>
          {submitted}
        </div>
      )}

      {isPaperMode && (
        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textAlign: "center" }}>
          Paper trading mode — no real funds
        </div>
      )}
    </div>
  );
}
