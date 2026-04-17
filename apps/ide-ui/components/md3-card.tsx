import clsx from "clsx";

type CardVariant = "elevated" | "filled" | "outlined";

interface MD3CardProps {
  variant?: CardVariant;
  className?: string;
  children: React.ReactNode;
  onClick?: () => void;
}

const variantStyles: Record<CardVariant, string> = {
  elevated: [
    "bg-[var(--md-sys-color-surface-variant)]",
    "shadow-[var(--md-sys-elevation-level1)]",
    "hover:shadow-[var(--md-sys-elevation-level2)]",
  ].join(" "),
  filled: "bg-[var(--md-sys-color-surface-container-high)]",
  outlined: [
    "bg-[var(--md-sys-color-surface)]",
    "border border-[var(--md-sys-color-outline)]",
  ].join(" "),
};

const base =
  "rounded-[var(--md-sys-shape-corner-medium)] p-5 transition-all duration-200";

export function MD3Card({
  variant = "elevated",
  className,
  children,
  onClick,
}: MD3CardProps) {
  return (
    <div
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") onClick();
            }
          : undefined
      }
      className={clsx(
        base,
        variantStyles[variant],
        onClick && "cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );
}
