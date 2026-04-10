import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { Size } from "@/lib/types";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: ReactNode;
  label: string; // accessible label (aria-label)
  size?: Size;
  active?: boolean;
}

const sizeMap: Record<Size, { dim: string; iconSize: number }> = {
  sm: { dim: "1.75rem", iconSize: 14 },
  md: { dim: "2.25rem", iconSize: 16 },
  lg: { dim: "2.75rem", iconSize: 20 },
};

export function IconButton({
  icon,
  label,
  size = "md",
  active = false,
  disabled,
  style,
  ...props
}: IconButtonProps) {
  const { dim } = sizeMap[size];
  return (
    <button
      {...props}
      aria-label={label}
      title={label}
      disabled={disabled}
      style={{
        width: dim,
        height: dim,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: "0.375rem",
        border: "none",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        background: active ? "var(--surface-active)" : "transparent",
        color: active ? "var(--accent-teal-400)" : "var(--text-muted)",
        transition: "background 0.15s, color 0.15s",
        flexShrink: 0,
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled && !active) {
          (e.currentTarget as HTMLButtonElement).style.background = "var(--surface-hover)";
          (e.currentTarget as HTMLButtonElement).style.color = "var(--text-primary)";
        }
        props.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        if (!disabled && !active) {
          (e.currentTarget as HTMLButtonElement).style.background = "transparent";
          (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
        }
        props.onMouseLeave?.(e);
      }}
    >
      {icon}
    </button>
  );
}
