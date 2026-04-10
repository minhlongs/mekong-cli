"use client";

// Agent Chat Panel — composes pipeline, messages, model status, input, footer

import { useState, useRef, useEffect } from "react";
import { PipelineVisualizer } from "./pipeline-visualizer";
import { ChatMessageItem } from "./chat-message";
import { ModelStatusCard } from "./model-status-card";
import { ChatInput } from "./chat-input";
import { ContextFooter } from "./context-footer";
import {
  MOCK_MESSAGES,
  MOCK_PIPELINE_STEPS,
  MOCK_MODEL_CONFIGS,
  MOCK_CONTEXT_FOOTER,
} from "@/lib/mock/agent-mock-data";
import type { ChatMessage } from "@/lib/agent-types";
import type { ModelVariant } from "@/lib/types";

export function AgentChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>(MOCK_MESSAGES);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function handleSend(content: string, model: ModelVariant) {
    const id = String(Date.now());
    setMessages((prev) => [
      ...prev,
      { id, role: "user", content, timestamp: Date.now() },
      // Placeholder echo for demo; replaced by real API in Phase 7
      {
        id: id + "_r",
        role: "agent",
        content: "Processing your request...",
        timestamp: Date.now() + 100,
        model,
      },
    ]);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Pipeline flow */}
      <PipelineVisualizer steps={MOCK_PIPELINE_STEPS} />

      {/* Message list */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "0.5rem 0.625rem",
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
        }}
      >
        {messages.map((msg) => (
          <ChatMessageItem key={msg.id} message={msg} />
        ))}
      </div>

      {/* Model status — compact 3-card stack */}
      <div
        style={{
          padding: "0.375rem 0.625rem",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          gap: "0.25rem",
          background: "var(--bg-secondary)",
        }}
      >
        {MOCK_MODEL_CONFIGS.map((m) => (
          <ModelStatusCard key={m.id} model={m} />
        ))}
      </div>

      {/* Input bar */}
      <ChatInput onSend={handleSend} />

      {/* Context footer */}
      <ContextFooter data={MOCK_CONTEXT_FOOTER} />
    </div>
  );
}
