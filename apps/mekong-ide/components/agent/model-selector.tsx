// Dropdown model selector — 4 models with color dot

import { ChevronDown } from "lucide-react";
import type { ModelVariant } from "@/lib/types";

interface ModelOption {
  id: ModelVariant;
  label: string;
  color: string;
}

const MODEL_OPTIONS: ModelOption[] = [
  { id: "architect", label: "Opus 4.6 (Architect)", color: "var(--model-architect)" },
  { id: "reasoning", label: "Sonnet 4.6 (Reasoning)", color: "var(--model-reasoning)" },
  { id: "audit", label: "Haiku (Audit)", color: "var(--model-audit)" },
  { id: "trading", label: "Qwen 3.5 (Trading)", color: "var(--model-trading)" },
];

interface ModelSelectorProps {
  value: ModelVariant;
  onChange: (model: ModelVariant) => void;
}

export function ModelSelector({ value, onChange }: ModelSelectorProps) {
  const selected = MODEL_OPTIONS.find((m) => m.id === value) ?? MODEL_OPTIONS[0];

  return (
    <div style={{ position: "relative" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.375rem",
          padding: "0.25rem 1.5rem 0.25rem 0.5rem",
          borderRadius: "0.25rem",
          background: "var(--bg-primary)",
          border: "1px solid var(--border-subtle)",
          cursor: "pointer",
        }}
      >
        <span
          style={{
            width: "0.5rem",
            height: "0.5rem",
            borderRadius: "50%",
            background: selected.color,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
          {selected.label}
        </span>
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as ModelVariant)}
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0,
          cursor: "pointer",
          width: "100%",
        }}
        aria-label="Select model"
      >
        {MODEL_OPTIONS.map((m) => (
          <option key={m.id} value={m.id}>
            {m.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={11}
        style={{
          position: "absolute",
          right: "0.375rem",
          top: "50%",
          transform: "translateY(-50%)",
          color: "var(--text-muted)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
