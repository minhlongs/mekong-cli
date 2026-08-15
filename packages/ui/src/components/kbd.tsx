"use client";

import * as React from "react";
import { cn } from "../lib/utils";

export interface KbdProps extends React.HTMLAttributes<HTMLElement> {}

const Kbd = React.forwardRef<HTMLElement, KbdProps>(
  ({ className, ...props }, ref) => (
    <kbd
      className={cn(
        "inlineFlex h5 itemsCenter justifyCenter rounded-[var(-RadiusSm)] border border-[var(-BorderStrong)] bg-[var(-BgSecondary)] px1.5 fontMono text-[0.625rem] fontMedium text-[var(-TextSecondary)] shadow-[var(-ShadowXs)]",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
Kbd.displayName = "Kbd";

export { Kbd };
