"use client";

/**
 * FairValueCacheTable — DataTable showing ticker, fair value, current price, edge %, confidence.
 * Edge colored green/red based on sign.
 */

import { DataTable } from "@/components/ds";
import type { FairValue } from "@/lib/types/trading-types";
import type { TableColumn, TableRow } from "@/lib/types";

interface FairValueCacheTableProps {
  fairValues: FairValue[];
}

const COLUMNS: TableColumn[] = [
  { key: "ticker", label: "Ticker", width: "80px" },
  { key: "fairValue", label: "Fair Value" },
  { key: "current", label: "Current" },
  { key: "edge", label: "Edge %" },
  { key: "confidence", label: "Conf." },
  { key: "updated", label: "Updated" },
];

function formatPrice(price: number): string {
  return price >= 1000 ? `$${price.toLocaleString()}` : `$${price.toFixed(2)}`;
}

export function FairValueCacheTable({ fairValues }: FairValueCacheTableProps) {
  const rows: TableRow[] = fairValues.map((fv) => {
    const edgePositive = fv.edgePct >= 0;
    const edgeColor = edgePositive ? "var(--status-success)" : "var(--status-danger)";
    const edgeSign = edgePositive ? "+" : "";

    return {
      ticker: (
        <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{fv.ticker}</span>
      ),
      fairValue: formatPrice(fv.fairValue),
      current: formatPrice(fv.currentPrice),
      edge: (
        <span style={{ color: edgeColor, fontWeight: 500 }}>
          {edgeSign}{fv.edgePct.toFixed(1)}%
        </span>
      ),
      confidence: (
        <span style={{ color: fv.confidence >= 80 ? "var(--status-success)" : fv.confidence >= 60 ? "var(--status-warning)" : "var(--text-muted)" }}>
          {fv.confidence}%
        </span>
      ),
      updated: (
        <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{fv.updatedAt}</span>
      ),
    };
  });

  return <DataTable columns={COLUMNS} rows={rows} emptyMessage="No fair value data" />;
}
