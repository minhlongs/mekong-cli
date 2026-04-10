import type { TableColumn, TableRow } from "@/lib/types";

interface DataTableProps {
  columns: TableColumn[];
  rows: TableRow[];
  emptyMessage?: string;
}

export function DataTable({ columns, rows, emptyMessage = "No data" }: DataTableProps) {
  return (
    <div
      style={{
        overflowX: "auto",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
      }}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            {columns.map((col) => (
              <th
                key={col.key}
                style={{
                  padding: "0.625rem 0.875rem",
                  textAlign: "left",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  width: col.width,
                  background: "var(--surface-card)",
                }}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{
                  padding: "2rem",
                  textAlign: "center",
                  color: "var(--text-muted)",
                  fontSize: "0.875rem",
                  background: "var(--bg-secondary)",
                }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={i}
                style={{
                  borderBottom: i < rows.length - 1 ? "1px solid var(--border-subtle)" : "none",
                  background: i % 2 === 0 ? "var(--bg-secondary)" : "var(--bg-primary)",
                }}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    style={{
                      padding: "0.625rem 0.875rem",
                      fontSize: "0.875rem",
                      color: "var(--text-primary)",
                    }}
                  >
                    {row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
