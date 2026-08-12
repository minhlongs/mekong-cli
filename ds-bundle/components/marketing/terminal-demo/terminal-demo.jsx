// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/marketing/terminal-demo.tsx
// Bundled in _ds_bundle.js as window.TerminalDemo

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
    const [lineIndex, setLineIndex] = React.useState(1);
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
          "wFull maxW2xl overflowHidden rounded-[var(-RadiusXl)] border border-[var(-ColorNeutral800)] bg-[var(-ColorNeutral950)] shadow-[var(-ShadowLg)]",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="flex itemsCenter gap2 borderB border-[var(-ColorNeutral800)] px4 py2.5">
          <span className="h3 w3 roundedFull bg-[var(-ColorDanger500)]" />
          <span className="h3 w3 roundedFull bg-[var(-ColorWarning500)]" />
          <span className="h3 w3 roundedFull bg-[var(-ColorSuccess500)]" />
          <span className="ml2 text-[var(-FontSizeXs)] text-[var(-ColorNeutral500)]">
            terminal
          </span>
        </div>
        <div className="p4 fontMono text-[var(-FontSizeSm)] leadingRelaxed">
          <div>
            <span className="text-[var(-ColorSuccess500)]">$ </span>
            <span className="text-[var(-ColorNeutral100)]">{displayed}</span>
            {showCursor && <span className="animatePulse text-[var(-Accent)]">|</span>}
          </div>
          {lineIndex >= 0 && lines.slice(0, lineIndex + 1).map((line, i) => (
            <div key={i} className="text-[var(-ColorNeutral400)]">{line}</div>
          ))}
        </div>
      </div>
    );
  }
);
TerminalDemo.displayName = "TerminalDemo";

export { TerminalDemo };
