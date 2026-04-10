/**
 * React hook for subscribing to a WebSocket channel.
 * Auto-connects on mount, disconnects on unmount.
 */
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getWsClient, type ConnectionState } from "./ws-client";
import type { WsChannel, WsEvent } from "./ws-events";

interface UseWsSubscriptionOptions {
  /** Filter to specific event types; undefined = receive all */
  eventTypes?: WsEvent["type"][];
  /** Max messages to buffer in state */
  bufferSize?: number;
}

interface UseWsSubscriptionResult<T extends WsEvent = WsEvent> {
  messages: T[];
  connectionState: ConnectionState;
  clearMessages: () => void;
}

export function useWsSubscription<T extends WsEvent = WsEvent>(
  channel: WsChannel,
  options: UseWsSubscriptionOptions = {}
): UseWsSubscriptionResult<T> {
  const { eventTypes, bufferSize = 100 } = options;
  const [messages, setMessages] = useState<T[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const bufferRef = useRef(bufferSize);
  bufferRef.current = bufferSize;

  useEffect(() => {
    const client = getWsClient(channel);
    client.connect();

    const unsubState = client.onStateChange(setConnectionState);
    setConnectionState(client.state);

    const unsubMsg = client.on((event) => {
      if (eventTypes && !eventTypes.includes(event.type)) return;
      setMessages((prev) => {
        const next = [...prev, event as T];
        return next.length > bufferRef.current
          ? next.slice(next.length - bufferRef.current)
          : next;
      });
    });

    return () => {
      unsubMsg();
      unsubState();
      // Do NOT disconnect — singleton clients persist across components
    };
  }, [channel]); // eslint-disable-line react-hooks/exhaustive-deps

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, connectionState, clearMessages };
}
