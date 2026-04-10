/**
 * Text block section — renders string content as pre-formatted text.
 * Monospace for code-like output; prose style for readable text.
 * Used by UniversalReportRenderer for sections of type "text".
 */

interface TextSectionProps {
  title?: string;
  /** String content to render; objects are pretty-printed as JSON */
  content: unknown;
  /** Render as monospace code block (default: false = prose) */
  mono?: boolean;
}

export function TextSection({ title, content, mono = false }: TextSectionProps) {
  const text =
    typeof content === "string" ? content
    : content === null || content === undefined ? "(empty)"
    : JSON.stringify(content, null, 2);

  return (
    <section style={{ marginBottom: "1.5rem" }}>
      {title && (
        <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          {title}
        </h2>
      )}
      <div
        style={{
          background: mono ? "var(--bg-tertiary)" : "var(--surface-card)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "0.5rem",
          padding: "0.875rem 1rem",
          fontSize: mono ? "0.8rem" : "0.875rem",
          fontFamily: mono ? "monospace" : "inherit",
          color: "var(--text-primary)",
          lineHeight: mono ? 1.6 : 1.7,
          whiteSpace: mono ? "pre-wrap" : "pre-line",
          overflowX: mono ? "auto" : undefined,
        }}
      >
        {text}
      </div>
    </section>
  );
}
