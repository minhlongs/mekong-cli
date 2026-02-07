import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export interface GlassContainerProps extends HTMLAttributes<HTMLDivElement> {
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
}

export const GlassContainer = forwardRef<HTMLDivElement, GlassContainerProps>(
  ({ className, maxWidth = "2xl", children, ...props }, ref) => {
    const maxWidthClasses = {
      sm: "max-w-screen-sm",
      md: "max-w-screen-md",
      lg: "max-w-screen-lg",
      xl: "max-w-screen-xl",
      "2xl": "max-w-screen-2xl",
      full: "max-w-full",
    };

    return (
      <div
        ref={ref}
        className={cn("mx-auto px-4 sm:px-6 lg:px-8", maxWidthClasses[maxWidth], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GlassContainer.displayName = "GlassContainer";
