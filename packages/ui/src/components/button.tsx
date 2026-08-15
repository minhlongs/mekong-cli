"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const buttonVariants = cva(
  "inlineFlex itemsCenter justifyCenter gap2 rounded-[var(-RadiusMd)] fontMedium transitionColors duration-[var(-DurationNormal)] focusVisible:outlineNone focusVisible:ring2 focusVisible:ring-[var(-Accent)] focusVisible:ringOffset2 disabled:pointerEventsNone disabled:opacity50",
  {
    variants: {
      variant: {
        default: "bg-[var(-Accent)] text-[var(-AccentText)] hover:bg-[var(-AccentHover)]",
        secondary: "bg-[var(-BgTertiary)] text-[var(-TextPrimary)] hover:bg-[var(-BgSecondary)]",
        ghost: "hover:bg-[var(-BgTertiary)] text-[var(-TextSecondary)]",
        danger: "bg-[var(-ColorDanger500)] textWhite hover:bg-[var(-ColorDanger600)]",
      },
      size: {
        sm: "h8 px3 text-[var(-FontSizeSm)]",
        md: "h10 px4 text-[var(-FontSizeBase)]",
        lg: "h12 px6 text-[var(-FontSizeLg)]",
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
