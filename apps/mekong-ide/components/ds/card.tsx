import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  header?: ReactNode;
  children: ReactNode;
  hoverable?: boolean;
}

export function Card({ header, children, hoverable = false, style, ...props }: CardProps) {
  return (
    <div
      {...props}
      style={{
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        overflow: "hidden",
        transition: hoverable ? "background 0.15s, border-color 0.15s" : undefined,
        cursor: hoverable ? "pointer" : undefined,
        ...style,
      }}
      onMouseEnter={(e) => {
        if (hoverable) {
          (e.currentTarget as HTMLDivElement).style.background = "var(--surface-hover)";
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-strong)";
        }
        props.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (hoverable) {
          (e.currentTarget as HTMLDivElement).style.background = "var(--surface-card)";
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-subtle)";
        }
        props.onMouseLeave?.(e);
      }}
    >
      {header && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderBottom: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
            fontSize: "0.75rem",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          {header}
        </div>
      )}
      <div style={{ padding: "1rem" }}>{children}</div>
    </div>
  );
}
