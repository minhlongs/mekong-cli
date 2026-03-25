"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface TerminalDemoProps extends React.HTMLAttributes<HTMLDivElement> {
  command?: string;
  lines?: string[];
  typingSpeed?: number;
}

const TerminalDemo = React.forwardRef<HTMLDivElement, TerminalDemoProps>(
  ({ className, command = 'mekong cook "Build landing page"', lines = [], typingSpeed = 50, ...props }, ref) => {
    const [displayed, setDisplayed] = React.useState("");
    const [lineIndex, setLineIndex] = React.useState(-1);
    const [showCursor, setShowCursor] = React.useState(true);

    React.useEffect(() => {
      let i = 0;
      const timer = setInterval(() => {
        if (i <= command.length) {
          setDisplayed(command.slice(0, i));
          i++;
        } else {
          clearInterval(timer);
          setTimeout(() => {
            setLineIndex(0);
            let li = 0;
            const lineTimer = setInterval(() => {
              if (li < lines.length) { setLineIndex(li); li++; }
              else { clearInterval(lineTimer); setShowCursor(false); }
            }, 400);
          }, 500);
        }
      }, typingSpeed);
      return () => clearInterval(timer);
    }, [command, lines, typingSpeed]);

    return (
      <div
        className={cn(
          "w-full max-w-2xl overflow-hidden rounded-[var(--radius-xl)] border border-[var(--color-neutral-800)] bg-[var(--color-neutral-950)] shadow-[var(--shadow-lg)]",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="flex items-center gap-2 border-b border-[var(--color-neutral-800)] px-4 py-2.5">
          <span className="h-3 w-3 rounded-full bg-[var(--color-danger-500)]" />
          <span className="h-3 w-3 rounded-full bg-[var(--color-warning-500)]" />
          <span className="h-3 w-3 rounded-full bg-[var(--color-success-500)]" />
          <span className="ml-2 text-[var(--font-size-xs)] text-[var(--color-neutral-500)]">
            terminal
          </span>
        </div>
        <div className="p-4 font-mono text-[var(--font-size-sm)] leading-relaxed">
          <div>
            <span className="text-[var(--color-success-500)]">$ </span>
            <span className="text-[var(--color-neutral-100)]">{displayed}</span>
            {showCursor && <span className="animate-pulse text-[var(--accent)]">|</span>}
          </div>
          {lineIndex >= 0 && lines.slice(0, lineIndex + 1).map((line, i) => (
            <div key={i} className="text-[var(--color-neutral-400)]">{line}</div>
          ))}
        </div>
      </div>
    );
  }
);
TerminalDemo.displayName = "TerminalDemo";

export { TerminalDemo };
