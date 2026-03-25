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
          "relative rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--color-neutral-950)]",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="flex items-center justify-between border-b border-[var(--color-neutral-800)] px-4 py-2">
          <span className="text-[var(--font-size-xs)] font-medium text-[var(--color-neutral-400)]">
            {language}
          </span>
          {showCopy && (
            <button
              onClick={handleCopy}
              className="text-[var(--font-size-xs)] text-[var(--color-neutral-400)] transition-colors duration-[var(--duration-fast)] hover:text-[var(--color-neutral-200)]"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          )}
        </div>
        <pre className="overflow-x-auto p-4">
          <code className="font-mono text-[var(--font-size-sm)] text-[var(--color-neutral-100)]">
            {code}
          </code>
        </pre>
      </div>
    );
  }
);
CodeBlock.displayName = "CodeBlock";

export { CodeBlock };
