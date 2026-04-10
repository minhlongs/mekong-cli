/**
 * Table section — renders an array-of-objects as MD3 DataTable.
 * Column headers derived from config.columns or first row keys.
 * Used by UniversalReportRenderer for sections of type "table".
 */

import { DataTable } from "@/components/ds";
import type { TableColumn, TableRow } from "@/lib/types";

interface TableSectionProps {
  title?: string;
  /** Array of row objects; first item keys used for auto-columns */
  rows: Record<string, unknown>[];
  /** Explicit ordered column keys; auto-derived when omitted */
  columnKeys?: string[];
}

function deriveColumns(rows: Record<string, unknown>[], columnKeys?: string[]): TableColumn[] {
  const keys = columnKeys ?? (rows.length > 0 ? Object.keys(rows[0]) : []);
  return keys.map((key) => ({
    key,
    label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
  }));
}

function toTableRows(rows: Record<string, unknown>[], columns: TableColumn[]): TableRow[] {
  return rows.map((row) => {
    const tableRow: TableRow = {};
    for (const col of columns) {
      const val = row[col.key];
      tableRow[col.key] = val === undefined || val === null ? "—" : String(val);
    }
    return tableRow;
  });
}

export function TableSection({ title, rows, columnKeys }: TableSectionProps) {
  const safeRows: Record<string, unknown>[] = Array.isArray(rows) ? rows : [];
  const columns = deriveColumns(safeRows, columnKeys);
  const tableRows = toTableRows(safeRows, columns);

  return (
    <section style={{ marginBottom: "1.5rem" }}>
      {title && (
        <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          {title}
        </h2>
      )}
      <DataTable columns={columns} rows={tableRows} emptyMessage="No data available" />
    </section>
  );
}
