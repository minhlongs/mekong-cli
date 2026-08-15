"use client";

import * as React from "react";
import { cn } from "../lib/utils";

export interface CodeBlockProps extends React.HTMLAttributes<HTMLDivElement> {
  code: string;
  language?: string;
  showCopy?: boolean;
}

const CodeBlock = React.forwardRef<HTMLDivElement, CodeBlockProps>(
  ({ className, code, language = "bash", showCopy = true, ...props }, ref) => {
    const [copied, setCopied] = React.useState(false);

    const handleCopy = React.useCallback(async () => {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }, [code]);

    return (
      <div
        className={cn(
          "relative rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-ColorNeutral950)]",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="flex itemsCenter justifyBetween borderB border-[var(-ColorNeutral800)] px4 py2">
          <span className="text-[var(-FontSizeXs)] fontMedium text-[var(-ColorNeutral400)]">
            {language}
          </span>
          {showCopy && (
            <button
              onClick={handleCopy}
              className="text-[var(-FontSizeXs)] text-[var(-ColorNeutral400)] transitionColors duration-[var(-DurationFast)] hover:text-[var(-ColorNeutral200)]"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          )}
        </div>
        <pre className="overflowXAuto p4">
          <code className="fontMono text-[var(-FontSizeSm)] text-[var(-ColorNeutral100)]">
            {code}
          </code>
        </pre>
      </div>
    );
  }
);
CodeBlock.displayName = "CodeBlock";

export { CodeBlock };
