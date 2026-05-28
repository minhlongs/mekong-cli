"use client";

import * as React from "react";
import { cn } from "../lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flexCol gap-[var(-Spacing1)]">
        {label && (
          <label htmlFor={inputId} className="text-[var(-FontSizeSm)] fontMedium text-[var(-TextPrimary)]">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <span className="absolute left3 top1/2 TranslateY1/2 text-[var(-TextTertiary)]">
              {icon}
            </span>
          )}
          <input
            id={inputId}
            className={cn(
              "flex h10 wFull rounded-[var(-RadiusMd)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] px3 py2 text-[var(-FontSizeBase)] text-[var(-TextPrimary)] placeholder:text-[var(-TextTertiary)] transitionColors duration-[var(-DurationFast)] focusVisible:outlineNone focusVisible:ring2 focusVisible:ring-[var(-Accent)] disabled:cursorNotAllowed disabled:opacity50",
              icon && "pl10",
              error && "border-[var(-ColorDanger500)] focusVisible:ring-[var(-ColorDanger500)]",
              className
            )}
            ref={ref}
            {...props}
          />
        </div>
        {error && (
          <p className="text-[var(-FontSizeSm)] text-[var(-ColorDanger500)]">{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
