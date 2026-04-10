"use client";

// Chat input bar: textarea + send + model selector

import { useState } from "react";
import { Send } from "lucide-react";
import { ModelSelector } from "./model-selector";
import type { ModelVariant } from "@/lib/types";

interface ChatInputProps {
  onSend: (content: string, model: ModelVariant) => void;
}

export function ChatInput({ onSend }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [model, setModel] = useState<ModelVariant>("reasoning");

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed, model);
    setValue("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div
      style={{
        padding: "0.5rem 0.75rem",
        borderTop: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        gap: "0.375rem",
      }}
    >
      {/* Model selector */}
      <ModelSelector value={model} onChange={setModel} />

      {/* Textarea + send */}
      <div style={{ display: "flex", gap: "0.375rem", alignItems: "flex-end" }}>
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask OpenClaw... (Enter to send)"
          rows={2}
          style={{
            flex: 1,
            resize: "none",
            fontSize: "0.75rem",
            padding: "0.375rem 0.5rem",
            borderRadius: "0.25rem",
            background: "var(--bg-primary)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-subtle)",
            fontFamily: "inherit",
            lineHeight: 1.5,
            outline: "none",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          aria-label="Send message"
          style={{
            padding: "0.375rem",
            borderRadius: "0.25rem",
            background: value.trim() ? "var(--accent-teal-500)" : "var(--surface-card)",
            color: value.trim() ? "var(--bg-primary)" : "var(--text-muted)",
            border: "none",
            cursor: value.trim() ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "background 0.15s",
          }}
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
