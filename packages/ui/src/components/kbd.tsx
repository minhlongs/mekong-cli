"use client";

import * as React from "react";
import { cn } from "../lib/utils";

export interface KbdProps extends React.HTMLAttributes<HTMLElement> {}

const Kbd = React.forwardRef<HTMLElement, KbdProps>(
  ({ className, ...props }, ref) => (
    <kbd
      className={cn(
        "inline-flex h-5 items-center justify-center rounded-[var(--radius-sm)] border border-[var(--border-strong)] bg-[var(--bg-secondary)] px-1.5 font-mono text-[0.625rem] font-medium text-[var(--text-secondary)] shadow-[var(--shadow-xs)]",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
Kbd.displayName = "Kbd";

export { Kbd };
