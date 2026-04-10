"use client";

// Agent Chat Panel — composes pipeline, messages, model status, input, footer

import { useRef, useEffect } from "react";
import { PipelineVisualizer } from "./pipeline-visualizer";
import { ChatMessageItem } from "./chat-message";
import { ModelStatusCard } from "./model-status-card";
import { ChatInput } from "./chat-input";
import { ContextFooter } from "./context-footer";
import { useAgentChat } from "@/hooks/use-agent-chat";
import {
  MOCK_PIPELINE_STEPS,
  MOCK_MODEL_CONFIGS,
  MOCK_CONTEXT_FOOTER,
} from "@/lib/mock/agent-mock-data";
import type { ModelVariant } from "@/lib/types";

export function AgentChatPanel() {
  const { messages, send, isLoading, isDemoMode, selectedModel, setSelectedModel } = useAgentChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function handleSend(content: string, model: ModelVariant) {
    // Sync model selection then send via hook (real API or demo fallback)
    setSelectedModel(model as string);
    send(content);
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
        {isLoading && (
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", padding: "0.25rem 0.5rem" }}>
            {isDemoMode ? "Demo mode…" : "Thinking…"}
          </div>
        )}
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
