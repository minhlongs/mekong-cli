"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const cardVariants = cva(
  "rounded-[var(-RadiusLg)] transitionShadow duration-[var(-DurationNormal)]",
  {
    variants: {
      variant: {
        default: "bg-[var(-BgPrimary)] border border-[var(-BorderDefault)]",
        elevated: "bg-[var(-BgPrimary)] shadow-[var(-ShadowMd)]",
        bordered: "bg-[var(-BgPrimary)] border2 border-[var(-BorderStrong)]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => (
    <div className={cn(cardVariants({ variant, className }))} ref={ref} {...props} />
  )
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div className={cn("flex flexCol gap-[var(-Spacing1)] p-[var(-Spacing6)]", className)} ref={ref} {...props} />
  )
);
CardHeader.displayName = "CardHeader";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div className={cn("px-[var(-Spacing6)] pb-[var(-Spacing6)]", className)} ref={ref} {...props} />
  )
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div className={cn("flex itemsCenter px-[var(-Spacing6)] pb-[var(-Spacing6)]", className)} ref={ref} {...props} />
  )
);
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardContent, CardFooter, cardVariants };
