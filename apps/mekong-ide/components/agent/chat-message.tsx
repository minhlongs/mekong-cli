// Single chat message — user / agent / system

import { Wrench } from "lucide-react";
import { Badge } from "@/components/ds";
import type { ChatMessage } from "@/lib/agent-types";
import type { ModelVariant } from "@/lib/types";

interface ChatMessageProps {
  message: ChatMessage;
}

// Map model variant to display label
const MODEL_LABELS: Record<ModelVariant, string> = {
  architect: "Opus 4.6",
  reasoning: "Sonnet 4.6",
  audit: "Haiku",
  trading: "Qwen 3.5",
};

export function ChatMessageItem({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.375rem",
          padding: "0.25rem 0.5rem",
          borderRadius: "0.25rem",
          background: "rgba(59,130,246,0.07)",
          border: "1px solid rgba(59,130,246,0.15)",
        }}
      >
        <Wrench size={11} style={{ color: "var(--status-info)", flexShrink: 0 }} />
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        gap: "0.25rem",
      }}
    >
      <div
        style={{
          maxWidth: "90%",
          borderRadius: "0.375rem",
          padding: "0.5rem 0.625rem",
          fontSize: "0.75rem",
          lineHeight: 1.5,
          background: isUser
            ? "rgba(20,184,166,0.12)"
            : "var(--surface-card)",
          color: "var(--text-primary)",
          border: `1px solid ${isUser ? "rgba(20,184,166,0.25)" : "var(--border-subtle)"}`,
        }}
      >
        {message.content}
      </div>
      {message.model && (
        <div style={{ paddingLeft: "0.125rem", paddingRight: "0.125rem" }}>
          <Badge variant={message.model} label={MODEL_LABELS[message.model]} dot />
        </div>
      )}
    </div>
  );
}
