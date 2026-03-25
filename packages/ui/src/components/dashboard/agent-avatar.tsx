"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

const agentColors: Record<string, string> = {
  G: "bg-[var(--color-success-500)]",  /* Git */
  F: "bg-[var(--color-info-500)]",     /* File */
  S: "bg-[var(--color-warning-500)]",  /* Shell */
  D: "bg-[var(--color-chart-5)]",      /* Docs */
  R: "bg-[var(--color-danger-500)]",   /* Review */
};

export interface AgentAvatarProps extends React.HTMLAttributes<HTMLSpanElement> {
  agent: string;
  size?: "sm" | "md" | "lg";
}

const sizeStyles = {
  sm: "h-5 w-5 text-[0.5rem]",
  md: "h-7 w-7 text-[0.625rem]",
  lg: "h-9 w-9 text-[var(--font-size-xs)]",
};

const AgentAvatar = React.forwardRef<HTMLSpanElement, AgentAvatarProps>(
  ({ className, agent, size = "md", ...props }, ref) => {
    const initial = agent[0]?.toUpperCase() ?? "?";
    const colorClass = agentColors[initial] ?? "bg-[var(--color-neutral-500)]";

    return (
      <span
        className={cn(
          "inline-flex items-center justify-center rounded-full font-bold text-white",
          sizeStyles[size],
          colorClass,
          className
        )}
        ref={ref}
        title={agent}
        {...props}
      >
        {initial}
      </span>
    );
  }
);
AgentAvatar.displayName = "AgentAvatar";

export { AgentAvatar };
