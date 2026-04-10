"use client";
import { useState } from "react";
import { Copy, Check } from "lucide-react";

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
}

export function CodeBlock({ code, language = "ts", showLineNumbers = true }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const lines = code.split("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      style={{
        position: "relative",
        background: "var(--bg-tertiary)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        overflow: "hidden",
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "0.375rem 0.75rem",
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--surface-card)",
        }}
      >
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
          {language}
        </span>
        <button
          onClick={handleCopy}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.25rem",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: copied ? "var(--status-success)" : "var(--text-muted)",
            fontSize: "0.7rem",
            padding: "0.125rem 0.25rem",
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      {/* Code body */}
      <pre style={{ margin: 0, padding: "0.75rem 0", overflowX: "auto" }}>
        {lines.map((line, i) => (
          <div key={i} style={{ display: "flex", minHeight: "1.4em" }}>
            {showLineNumbers && (
              <span
                style={{
                  minWidth: "2.5rem",
                  paddingRight: "1rem",
                  textAlign: "right",
                  color: "var(--text-muted)",
                  fontSize: "0.8rem",
                  userSelect: "none",
                  flexShrink: 0,
                  paddingLeft: "0.75rem",
                }}
              >
                {i + 1}
              </span>
            )}
            <code
              style={{
                fontSize: "0.8rem",
                color: "var(--text-primary)",
                paddingRight: "1rem",
                paddingLeft: showLineNumbers ? 0 : "0.75rem",
                whiteSpace: "pre",
                fontFamily: "monospace",
              }}
            >
              {line}
            </code>
          </div>
        ))}
      </pre>
    </div>
  );
}
