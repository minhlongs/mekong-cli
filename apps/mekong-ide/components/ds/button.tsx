import type { ButtonHTMLAttributes } from "react";
import type { ButtonVariant, Size } from "@/lib/types";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: Size;
  loading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: `background:var(--accent-teal-500);color:var(--bg-primary);border:1px solid transparent`,
  secondary: `background:var(--surface-card);color:var(--text-primary);border:1px solid var(--border-strong)`,
  danger: `background:var(--status-danger);color:#fff;border:1px solid transparent`,
  ghost: `background:transparent;color:var(--text-secondary);border:1px solid transparent`,
};

const sizeStyles: Record<Size, string> = {
  sm: "0.25rem 0.625rem;font-size:0.75rem;",
  md: "0.5rem 1rem;font-size:0.875rem;",
  lg: "0.625rem 1.25rem;font-size:1rem;",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  children,
  style,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;
  return (
    <button
      {...props}
      disabled={isDisabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.375rem",
        padding: size === "sm" ? "0.25rem 0.625rem" : size === "lg" ? "0.625rem 1.25rem" : "0.5rem 1rem",
        fontSize: size === "sm" ? "0.75rem" : size === "lg" ? "1rem" : "0.875rem",
        fontWeight: 500,
        borderRadius: "0.375rem",
        cursor: isDisabled ? "not-allowed" : "pointer",
        opacity: isDisabled ? 0.5 : 1,
        transition: "opacity 0.15s, background 0.15s",
        background:
          variant === "primary" ? "var(--accent-teal-500)"
          : variant === "danger" ? "var(--status-danger)"
          : variant === "secondary" ? "var(--surface-card)"
          : "transparent",
        color:
          variant === "primary" || variant === "danger" ? "#fff"
          : variant === "ghost" ? "var(--text-secondary)"
          : "var(--text-primary)",
        border:
          variant === "secondary" ? "1px solid var(--border-strong)" : "1px solid transparent",
        ...style,
      }}
    >
      {loading ? "..." : children}
    </button>
  );
}
