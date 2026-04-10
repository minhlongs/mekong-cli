import type { BadgeVariant } from "@/lib/types";

interface BadgeProps {
  variant: BadgeVariant;
  label: string;
  dot?: boolean;
}

const colorMap: Record<BadgeVariant, { bg: string; text: string }> = {
  success:   { bg: "rgba(34,197,94,0.15)",  text: "var(--status-success)" },
  warning:   { bg: "rgba(234,179,8,0.15)",  text: "var(--status-warning)" },
  danger:    { bg: "rgba(239,68,68,0.15)",  text: "var(--status-danger)" },
  info:      { bg: "rgba(59,130,246,0.15)", text: "var(--status-info)" },
  architect: { bg: "rgba(139,92,246,0.15)", text: "var(--model-architect)" },
  reasoning: { bg: "rgba(245,158,11,0.15)", text: "var(--model-reasoning)" },
  audit:     { bg: "rgba(99,102,241,0.15)", text: "var(--model-audit)" },
  trading:   { bg: "rgba(16,185,129,0.15)", text: "var(--model-trading)" },
};

export function Badge({ variant, label, dot = false }: BadgeProps) {
  const { bg, text } = colorMap[variant];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.25rem",
        padding: "0.125rem 0.5rem",
        borderRadius: "9999px",
        fontSize: "0.75rem",
        fontWeight: 500,
        background: bg,
        color: text,
        lineHeight: 1.5,
      }}
    >
      {dot && (
        <span
          style={{
            width: "0.375rem",
            height: "0.375rem",
            borderRadius: "50%",
            background: text,
            flexShrink: 0,
          }}
        />
      )}
      {label}
    </span>
  );
}
