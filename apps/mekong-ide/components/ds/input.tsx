import type { InputHTMLAttributes } from "react";
import { Search } from "lucide-react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  search?: boolean;
}

export function Input({ label, error, search = false, id, style, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 500 }}
        >
          {label}
        </label>
      )}
      <div style={{ position: "relative" }}>
        {search && (
          <Search
            size={14}
            style={{
              position: "absolute",
              left: "0.625rem",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-muted)",
              pointerEvents: "none",
            }}
          />
        )}
        <input
          id={inputId}
          {...props}
          style={{
            width: "100%",
            padding: search ? "0.5rem 0.75rem 0.5rem 2rem" : "0.5rem 0.75rem",
            fontSize: "0.875rem",
            background: "var(--surface-card)",
            color: "var(--text-primary)",
            border: `1px solid ${error ? "var(--status-danger)" : "var(--border-strong)"}`,
            borderRadius: "0.375rem",
            outline: "none",
            ...style,
          }}
        />
      </div>
      {error && (
        <span style={{ fontSize: "0.75rem", color: "var(--status-danger)" }}>{error}</span>
      )}
    </div>
  );
}
