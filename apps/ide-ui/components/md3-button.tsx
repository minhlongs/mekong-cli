import { type AnchorHTMLAttributes, type ButtonHTMLAttributes } from "react";
import clsx from "clsx";

type Variant = "filled" | "outlined" | "text" | "tonal";

interface MD3ButtonBaseProps {
  variant?: Variant;
  className?: string;
  children: React.ReactNode;
}

type MD3ButtonProps =
  | (MD3ButtonBaseProps &
      ButtonHTMLAttributes<HTMLButtonElement> & { href?: undefined })
  | (MD3ButtonBaseProps &
      AnchorHTMLAttributes<HTMLAnchorElement> & {
        href: string;
        target?: string;
        rel?: string;
      });

const variantStyles: Record<Variant, string> = {
  filled: [
    "bg-[var(--md-sys-color-primary)]",
    "text-[var(--md-sys-color-on-primary)]",
    "hover:opacity-90",
    "shadow-[var(--md-sys-elevation-level1)]",
  ].join(" "),
  outlined: [
    "border border-[var(--md-sys-color-outline)]",
    "text-[var(--md-sys-color-primary)]",
    "hover:bg-[var(--md-sys-color-surface-container)]",
  ].join(" "),
  text: [
    "text-[var(--md-sys-color-primary)]",
    "hover:bg-[var(--md-sys-color-surface-container)]",
  ].join(" "),
  tonal: [
    "bg-[var(--md-sys-color-secondary-container)]",
    "text-[var(--md-sys-color-on-secondary-container)]",
    "hover:opacity-90",
  ].join(" "),
};

const base =
  "inline-flex items-center justify-center gap-2 px-6 py-2.5 m3-label-large rounded-[var(--md-sys-shape-corner-full)] transition-all duration-200 cursor-pointer select-none";

export function MD3Button(props: MD3ButtonProps) {
  const { variant = "filled", className, children, ...rest } = props;
  const classes = clsx(base, variantStyles[variant], className);

  if ("href" in rest && rest.href !== undefined) {
    const { href, target, rel, ...anchorRest } = rest as {
      href: string;
      target?: string;
      rel?: string;
      [key: string]: unknown;
    };
    return (
      <a
        href={href}
        target={target}
        rel={rel}
        className={classes}
        {...(anchorRest as AnchorHTMLAttributes<HTMLAnchorElement>)}
      >
        {children}
      </a>
    );
  }

  return (
    <button
      className={classes}
      {...(rest as ButtonHTMLAttributes<HTMLButtonElement>)}
    >
      {children}
    </button>
  );
}
