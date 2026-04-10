/**
 * JSON fallback section — renders raw result_data when no layout is defined
 * or when an unknown section type is encountered.
 * Uses DS CodeBlock for syntax-highlighted output with copy button.
 */

"use client";
import { CodeBlock } from "@/components/ds";

interface ReportFallbackJsonProps {
  data: unknown;
  label?: string;
}

export function ReportFallbackJson({ data, label = "Raw Output" }: ReportFallbackJsonProps) {
  const json = JSON.stringify(data, null, 2);

  return (
    <section style={{ marginBottom: "1.5rem" }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.75rem" }}>
        {label}
      </h2>
      <CodeBlock code={json} language="json" showLineNumbers={false} />
    </section>
  );
}
