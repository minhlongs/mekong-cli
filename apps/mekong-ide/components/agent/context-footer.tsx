// Context footer: token bar + cache hits + cost

import { ProgressBar } from "@/components/ds";
import type { ContextFooterData } from "@/lib/agent-types";

interface ContextFooterProps {
  data: ContextFooterData;
}

function formatTokens(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n);
}

export function ContextFooter({ data }: ContextFooterProps) {
  const pct = Math.round((data.tokensUsed / data.tokenLimit) * 100);
  const variant = pct >= 80 ? "danger" : pct >= 60 ? "warning" : "accent";

  return (
    <div
      style={{
        padding: "0.5rem 0.75rem",
        borderTop: "1px solid var(--border-subtle)",
        background: "var(--bg-primary)",
        display: "flex",
        flexDirection: "column",
        gap: "0.375rem",
      }}
    >
      {/* Token bar */}
      <ProgressBar value={pct} variant={variant} showPercent={false} />

      {/* Stats row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
          {formatTokens(data.tokensUsed)} / {formatTokens(data.tokenLimit)} tokens
        </span>
        <div style={{ display: "flex", gap: "0.625rem" }}>
          <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
            {data.cacheHits} cache hits
          </span>
          <span style={{ fontSize: "0.65rem", color: "var(--status-success)" }}>
            ${data.estimatedCost.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}
