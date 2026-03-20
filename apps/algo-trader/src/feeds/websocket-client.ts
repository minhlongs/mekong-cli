/**
 * Base WebSocket Client
 * Foundation for exchange-specific WebSocket connections
 * Features: auto-reconnect, heartbeat, rate limit handling
 */

export interface WebSocketMessage {
  type: 'orderbook' | 'trade' | 'ticker' | 'heartbeat' | 'error';
  exchange: string;
  symbol: string;
  data: unknown;
  timestamp: number;
}

export interface WebSocketConfig {
  url: string;
  reconnectDelay: number;
  maxReconnectDelay: number;
  heartbeatInterval: number;
  reconnectMultiplier: number;
}

export abstract class BaseWebSocketClient {
  protected ws: WebSocket | null = null;
  protected config: WebSocketConfig;
  protected reconnectAttempts = 0;
  protected heartbeatTimer: NodeJS.Timeout | null = null;
  protected messageHandlers: Set<(msg: WebSocketMessage) => void> = new Set();
  protected state: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' = 'disconnected';

  constructor(config: Partial<WebSocketConfig>) {
    this.config = {
      url: config.url || '',
      reconnectDelay: config.reconnectDelay || 1000,
      maxReconnectDelay: config.maxReconnectDelay || 30000,
      heartbeatInterval: config.heartbeatInterval || 30000,
      reconnectMultiplier: config.reconnectMultiplier || 2,
    };
  }

  abstract connect(): Promise<void>;
  abstract disconnect(): Promise<void>;
  abstract subscribe(symbols: string[]): Promise<void>;
  abstract unsubscribe(symbols: string[]): Promise<void>;

  protected abstract handleMessage(data: unknown): WebSocketMessage | null;
  protected abstract getSubscriptions(symbols: string[]): unknown;

  public onMessage(handler: (msg: WebSocketMessage) => void): void {
    this.messageHandlers.add(handler);
  }

  public offMessage(handler: (msg: WebSocketMessage) => void): void {
    this.messageHandlers.delete(handler);
  }

  public getState(): 'connecting' | 'connected' | 'disconnected' | 'reconnecting' {
    return this.state;
  }

  protected async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.url);

        this.ws.onopen = () => {
          this.state = 'connected';
          this.reconnectAttempts = 0;
          console.log(`[WebSocket] Connected to ${this.config.url}`);
          this.startHeartbeat();
          resolve();
        };

        this.ws.onclose = () => {
          this.state = 'disconnected';
          this.stopHeartbeat();
          console.log(`[WebSocket] Disconnected from ${this.config.url}`);
          this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error(`[WebSocket] Error:`, error);
          this.state = 'disconnected';
          reject(error);
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data as string);
          const message = this.handleMessage(data);
          if (message) {
            this.messageHandlers.forEach((handler) => handler(message));
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  protected sendMessage(message: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= 10) {
      console.error('[WebSocket] Max reconnection attempts reached');
      return;
    }

    this.state = 'reconnecting';
    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(this.config.reconnectMultiplier, this.reconnectAttempts),
      this.config.maxReconnectDelay
    );

    this.reconnectAttempts++;
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }

  protected startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.config.heartbeatInterval);
  }

  protected stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  protected abstract sendHeartbeat(): void;
}
