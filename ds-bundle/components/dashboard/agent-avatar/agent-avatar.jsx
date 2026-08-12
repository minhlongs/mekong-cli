// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/dashboard/agent-avatar.tsx
// Bundled in _ds_bundle.js as window.AgentAvatar

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

const agentColors: Record<string, string> = {
  G: "bg-[var(-ColorSuccess500)]",  /* Git */
  F: "bg-[var(-ColorInfo500)]",     /* File */
  S: "bg-[var(-ColorWarning500)]",  /* Shell */
  D: "bg-[var(-ColorChart5)]",      /* Docs */
  R: "bg-[var(-ColorDanger500)]",   /* Review */
};

export interface AgentAvatarProps extends React.HTMLAttributes<HTMLSpanElement> {
  agent: string;
  size?: "sm" | "md" | "lg";
}

const sizeStyles = {
  sm: "h5 w5 text-[0.5rem]",
  md: "h7 w7 text-[0.625rem]",
  lg: "h9 w9 text-[var(-FontSizeXs)]",
};

const AgentAvatar = React.forwardRef<HTMLSpanElement, AgentAvatarProps>(
  ({ className, agent, size = "md", ...props }, ref) => {
    const initial = agent[0]?.toUpperCase() ?? "?";
    const colorClass = agentColors[initial] ?? "bg-[var(-ColorNeutral500)]";

    return (
      <span
        className={cn(
          "inlineFlex itemsCenter justifyCenter roundedFull fontBold textWhite",
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
