/**
 * WebSocket event type definitions for all real-time channels.
 */

export type WsChannel = "/ws/chat" | "/ws/events";

// ---- Chat channel ----

export interface ChatMessageEvent {
  type: "chat.message";
  payload: {
    id: string;
    role: "user" | "agent" | "system";
    content: string;
    timestamp: number;
    model?: string;
    /** True when this is a streaming chunk, false on final */
    streaming?: boolean;
  };
}

// ---- Events channel ----

export interface ToolCallEvent {
  type: "tool.call";
  payload: {
    id: string;
    toolId: string;
    toolName: string;
    args: Record<string, unknown>;
    status: "running" | "complete" | "error";
    result?: string;
    durationMs?: number;
    timestamp: number;
  };
}

export interface EngineStatusEvent {
  type: "engine.status";
  payload: {
    engineId: string;
    status: "running" | "idle" | "stopped" | "error";
    tokensPerSec?: number;
    latencyMs?: number;
  };
}

export interface SignalEvent {
  type: "trading.signal";
  payload: {
    id: string;
    ticker: string;
    direction: "buy" | "sell" | "hold";
    confidence: number;
    model: string;
    timestamp: string;
  };
}

export interface ContextUpdateEvent {
  type: "context.update";
  payload: {
    tokensUsed: number;
    tokenLimit: number;
    compressionTriggered?: boolean;
  };
}

export interface PingEvent {
  type: "ping";
  payload: { ts: number };
}

export type WsEvent =
  | ChatMessageEvent
  | ToolCallEvent
  | EngineStatusEvent
  | SignalEvent
  | ContextUpdateEvent
  | PingEvent;
