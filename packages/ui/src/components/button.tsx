"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] font-medium transition-colors duration-[var(--duration-normal)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[var(--accent)] text-[var(--accent-text)] hover:bg-[var(--accent-hover)]",
        secondary: "bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]",
        ghost: "hover:bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
        danger: "bg-[var(--color-danger-500)] text-white hover:bg-[var(--color-danger-600)]",
      },
      size: {
        sm: "h-8 px-3 text-[var(--font-size-sm)]",
        md: "h-10 px-4 text-[var(--font-size-base)]",
        lg: "h-12 px-6 text-[var(--font-size-lg)]",
      },
    },
    defaultVariants: { variant: "default", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  )
);
Button.displayName = "Button";

export { Button, buttonVariants };
