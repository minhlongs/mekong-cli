/**
 * Agent chat hook — manages message list, sends messages, handles WS stream.
 */
"use client";

import { useState, useCallback, useEffect } from "react";
import { sendMessage } from "@/lib/api/endpoints/agent-api";
import { useWsSubscription } from "@/lib/ws/use-ws-subscription";
import type { ChatMessage } from "@/lib/agent-types";
import type { ChatMessageEvent } from "@/lib/ws/ws-events";
import { MOCK_MESSAGES, MOCK_MODEL_CONFIGS } from "@/lib/mock/agent-mock-data";
import { isApiReachable } from "@/lib/api/demo-mode";

interface UseAgentChatResult {
  messages: ChatMessage[];
  isLoading: boolean;
  isDemoMode: boolean;
  sessionId: string | null;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  send: (content: string) => Promise<void>;
}

export function useAgentChat(): UseAgentChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>(MOCK_MODEL_CONFIGS[0]?.id ?? "architect");

  // Bootstrap with mock data in demo mode
  useEffect(() => {
    isApiReachable().then((ok) => {
      if (!ok) {
        setMessages(MOCK_MESSAGES);
        setIsDemoMode(true);
      }
    });
  }, []);

  // Subscribe to WS chat events for streaming responses
  const { messages: wsMessages } = useWsSubscription<ChatMessageEvent>("/ws/chat", {
    eventTypes: ["chat.message"],
  });

  useEffect(() => {
    if (wsMessages.length === 0) return;
    const latest = wsMessages[wsMessages.length - 1];
    setMessages((prev) => {
      const existing = prev.findIndex((m) => m.id === latest.payload.id);
      const updated: ChatMessage = {
        id: latest.payload.id,
        role: latest.payload.role,
        content: latest.payload.content,
        timestamp: latest.payload.timestamp,
        model: latest.payload.model as ChatMessage["model"],
      };
      if (existing >= 0) {
        return prev.map((m, i) => (i === existing ? updated : m));
      }
      return [...prev, updated];
    });
  }, [wsMessages]);

  const send = useCallback(
    async (content: string) => {
      if (isDemoMode) {
        // Simulate reply in demo mode
        const userMsg: ChatMessage = {
          id: `demo-${Date.now()}`,
          role: "user",
          content,
          timestamp: Date.now(),
        };
        const replyMsg: ChatMessage = {
          id: `demo-reply-${Date.now()}`,
          role: "agent",
          content: "[DEMO] API unreachable — running in demo mode.",
          timestamp: Date.now() + 500,
          model: "architect",
        };
        setMessages((prev) => [...prev, userMsg, replyMsg]);
        return;
      }
      const userMsg: ChatMessage = {
        id: `optimistic-${Date.now()}`,
        role: "user",
        content,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      const result = await sendMessage({ content, sessionId: sessionId ?? undefined, model: selectedModel });
      setIsLoading(false);
      if (result.error) return;
      if (result.data) setSessionId(result.data.sessionId);
    },
    [isDemoMode, sessionId, selectedModel]
  );

  return { messages, isLoading, isDemoMode, sessionId, selectedModel, setSelectedModel, send };
}
