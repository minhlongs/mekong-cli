/**
 * WebSocket connection manager with automatic reconnect (exponential backoff).
 * Emits typed WsEvent objects to registered listeners.
 */

import { WS_BASE_URL } from "../api/api-config";
import { getAuthToken } from "../api/api-config";
import type { WsChannel, WsEvent } from "./ws-events";

type WsListener = (event: WsEvent) => void;
type ConnectionState = "disconnected" | "connecting" | "connected" | "reconnecting";

const MAX_BACKOFF_MS = 30_000;
const INITIAL_BACKOFF_MS = 1_000;

class WsChannelClient {
  private socket: WebSocket | null = null;
  private listeners = new Set<WsListener>();
  private stateListeners = new Set<(state: ConnectionState) => void>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private backoffMs = INITIAL_BACKOFF_MS;
  private _state: ConnectionState = "disconnected";
  private shouldReconnect = false;

  constructor(private readonly channel: WsChannel) {}

  get state(): ConnectionState {
    return this._state;
  }

  private setState(next: ConnectionState) {
    this._state = next;
    this.stateListeners.forEach((fn) => fn(next));
  }

  connect() {
    if (this._state === "connected" || this._state === "connecting") return;
    this.shouldReconnect = true;
    this.openSocket();
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.socket?.close(1000, "client disconnect");
    this.socket = null;
    this.setState("disconnected");
  }

  private openSocket() {
    this.setState(this._state === "disconnected" ? "connecting" : "reconnecting");
    const token = getAuthToken();
    const url = `${WS_BASE_URL}${this.channel}${token ? `?token=${token}` : ""}`;

    try {
      this.socket = new WebSocket(url);
    } catch (_) {
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      this.backoffMs = INITIAL_BACKOFF_MS;
      this.setState("connected");
    };

    this.socket.onmessage = (ev: MessageEvent) => {
      try {
        const event = JSON.parse(ev.data as string) as WsEvent;
        this.listeners.forEach((fn) => fn(event));
      } catch (_) {
        // ignore malformed messages
      }
    };

    this.socket.onerror = () => {
      // onclose fires after onerror, handles reconnect
    };

    this.socket.onclose = () => {
      this.socket = null;
      if (this.shouldReconnect) this.scheduleReconnect();
      else this.setState("disconnected");
    };
  }

  private scheduleReconnect() {
    this.setState("reconnecting");
    this.reconnectTimer = setTimeout(() => {
      this.backoffMs = Math.min(this.backoffMs * 2, MAX_BACKOFF_MS);
      this.openSocket();
    }, this.backoffMs);
  }

  on(listener: WsListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onStateChange(listener: (state: ConnectionState) => void): () => void {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }

  send(data: unknown) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }
}

/** Singleton clients per channel */
const clients: Partial<Record<WsChannel, WsChannelClient>> = {};

export function getWsClient(channel: WsChannel): WsChannelClient {
  if (!clients[channel]) {
    clients[channel] = new WsChannelClient(channel);
  }
  return clients[channel]!;
}

export type { ConnectionState, WsListener };
