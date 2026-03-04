/**
 * Webhook Notifier with Retry and Circuit Breaker Support
 * Handles reliable webhook delivery with automatic retry and failure protection
 */

import { logger } from '../utils/logger';
import { RetryHandler, RetryConfig } from './retry-handler';
import { CircuitBreaker, CircuitBreakerConfig } from './circuit-breaker';

export interface WebhookConfig {
  url: string;
  eventType: string | string[];
  headers?: Record<string, string>;
  timeoutMs?: number;
  retryConfig?: RetryConfig;
  circuitBreakerConfig?: CircuitBreakerConfig;
}

export interface WebhookPayload {
  event: string;
  timestamp: number;
  data: any;
  signature?: string; // Optional HMAC signature
}

export interface WebhookRegistration {
  url: string;
  eventTypes: string[];
  headers?: Record<string, string>;
  createdAt: number;
}

export interface WebhookDeliveryResult {
  success: boolean;
  statusCode?: number;
  error?: string;
  deliveredAt: number;
  attempts: number;
}

export class WebhookNotifier {
  private retryHandler?: RetryHandler;
  private circuitBreaker?: CircuitBreaker;
  private registeredWebhooks: Map<string, WebhookRegistration[]> = new Map();
  private readonly defaultTimeoutMs: number = 10000;

  constructor(
    private config: {
      hmacSecret?: string; // Secret for HMAC signatures
      maxConcurrentDeliveries?: number;
    } = {}
  ) {}

  /**
   * Register a webhook for specific event types
   */
  registerWebhook(webhookConfig: WebhookConfig): void {
    const { url, eventType, headers } = webhookConfig;
    const eventTypes = Array.isArray(eventType) ? eventType : [eventType];

    if (!this.registeredWebhooks.has(url)) {
      this.registeredWebhooks.set(url, []);
    }

    const registrations = this.registeredWebhooks.get(url)!;

    // Initialize retry and circuit breaker if configured
    if (webhookConfig.retryConfig) {
      this.retryHandler = new RetryHandler(webhookConfig.retryConfig);
    }

    if (webhookConfig.circuitBreakerConfig) {
      this.circuitBreaker = new CircuitBreaker(webhookConfig.circuitBreakerConfig);
    }

    registrations.push({
      url,
      eventTypes,
      headers,
      createdAt: Date.now()
    });

    logger.info(`Webhook registered: ${url} [${eventTypes.join(', ')}]`);
  }

  /**
   * Unregister a webhook
   */
  unregisterWebhook(url: string, eventType?: string | string[]): void {
    if (!this.registeredWebhooks.has(url)) {
      return;
    }

    if (!eventType) {
      // Remove all registrations for this URL
      this.registeredWebhooks.delete(url);
      logger.info(`Webhook unregistered: ${url}`);
      return;
    }

    const eventTypes = Array.isArray(eventType) ? eventType : [eventType];
    const registrations = this.registeredWebhooks.get(url)!;

    // Remove specific event types
    const filteredRegistrations = registrations.filter(reg =>
      !reg.eventTypes.some(et => eventTypes.includes(et))
    );

    if (filteredRegistrations.length === 0) {
      this.registeredWebhooks.delete(url);
    } else {
      this.registeredWebhooks.set(url, filteredRegistrations);
    }

    logger.info(`Webhook unregistered: ${url} [${eventTypes.join(', ')}]`);
  }

  /**
   * Deliver a payload to all registered webhooks for the specified event type
   */
  async deliverToEvent(event: string, data: any): Promise<WebhookDeliveryResult[]> {
    const matchingWebhooks = this.getMatchingWebhooks(event);
    const results: WebhookDeliveryResult[] = [];

    for (const webhook of matchingWebhooks) {
      try {
        const result = await this.deliverToSingleWebhook(
          webhook.url,
          { event, timestamp: Date.now(), data },
          webhook.headers
        );
        results.push(result);
      } catch (error) {
        results.push({
          success: false,
          error: error instanceof Error ? error.message : String(error),
          deliveredAt: Date.now(),
          attempts: 0
        });
      }
    }

    return results;
  }

  /**
   * Deliver a payload to a specific webhook URL
   */
  async deliverToSingleWebhook(
    url: string,
    payload: WebhookPayload,
    headers?: Record<string, string>
  ): Promise<WebhookDeliveryResult> {
    const deliveryStart = Date.now();
    let attempts = 0;
    let lastError: any;

    try {
      // Create signed payload if HMAC secret is configured
      const signedPayload = this.signPayload(payload);

      if (this.circuitBreaker) {
        // Use circuit breaker to wrap the delivery
        return await this.circuitBreaker.execute(async () => {
          return await this.performDelivery(url, signedPayload, deliveryStart, headers);
        });
      } else {
        // Perform direct delivery without circuit breaker
        return await this.performDelivery(url, signedPayload, deliveryStart, headers);
      }
    } catch (error) {
      lastError = error;
      logger.error(`Webhook delivery failed to ${url}: ${error instanceof Error ? error.message : String(error)}`);

      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        deliveredAt: Date.now(),
        attempts: attempts
      };
    }
  }

  /**
   * Internal method to perform the actual HTTP delivery with optional retry
   */
  private async performDelivery(
    url: string,
    payload: WebhookPayload,
    deliveryStart: number,
    headers?: Record<string, string>
  ): Promise<WebhookDeliveryResult> {
    let attempts = 0;
    // Initialize with default failure result
    let result: WebhookDeliveryResult = {
      success: false,
      deliveredAt: Date.now(),
      attempts: 0
    };

    if (this.retryHandler) {
      // Use retry handler for delivery
      try {
        await this.retryHandler.execute(async () => {
          attempts++;
          const response = await this.makeHttpRequest(url, payload, headers);

          if (response.ok) {
            result = {
              success: true,
              statusCode: response.status,
              deliveredAt: Date.now(),
              attempts: attempts
            };
            return result;
          } else {
            // Throw error to trigger retry
            const errorText = await response.text().catch(() => 'Unknown error');
            throw new Error(`HTTP ${response.status}: ${errorText}`);
          }
        });
      } catch (error) {
        // If retries exhausted, return failure
        result = {
          success: false,
          error: error instanceof Error ? error.message : String(error),
          deliveredAt: Date.now(),
          attempts: attempts
        };
      }
    } else {
      // No retry - single delivery attempt
      attempts = 1;
      try {
        const response = await this.makeHttpRequest(url, payload, headers);

        if (response.ok) {
          result = {
            success: true,
            statusCode: response.status,
            deliveredAt: Date.now(),
            attempts: attempts
          };
        } else {
          const errorText = await response.text().catch(() => 'Unknown error');
          result = {
            success: false,
            statusCode: response.status,
            error: `HTTP ${response.status}: ${errorText}`,
            deliveredAt: Date.now(),
            attempts: attempts
          };
        }
      } catch (error) {
        result = {
          success: false,
          error: error instanceof Error ? error.message : String(error),
          deliveredAt: Date.now(),
          attempts: attempts
        };
      }
    }

    return result;
  }

  /**
   * Make the actual HTTP request to deliver the webhook
   */
  private async makeHttpRequest(
    url: string,
    payload: WebhookPayload,
    headers?: Record<string, string>
  ): Promise<Response> {
    const timeoutMs = this.defaultTimeoutMs;

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(headers || {})
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      if (controller.signal.aborted) {
        throw new Error(`Webhook request to ${url} timed out after ${timeoutMs}ms`);
      }

      throw error;
    }
  }

  /**
   * Get all registered webhooks that match the specified event type
   */
  private getMatchingWebhooks(event: string): WebhookRegistration[] {
    const matches: WebhookRegistration[] = [];

    for (const [url, registrations] of this.registeredWebhooks.entries()) {
      for (const reg of registrations) {
        if (reg.eventTypes.includes(event) || reg.eventTypes.includes('*')) {
          matches.push(reg);
        }
      }
    }

    return matches;
  }

  /**
   * Sign payload with HMAC if secret is configured
   */
  private signPayload(payload: WebhookPayload): WebhookPayload {
    if (!this.config.hmacSecret) {
      return payload;
    }

    // In a real implementation, you would calculate the HMAC signature
    // For now, we'll just return the payload as-is
    // The actual signature calculation would involve:
    // 1. Serializing the payload to a string
    // 2. Creating HMAC SHA256 hash with the secret
    // 3. Encoding it appropriately

    return {
      ...payload,
      signature: `dummy-signature-${Date.now()}` // Placeholder
    };
  }

  /**
   * Get registered webhooks for monitoring/debugging
   */
  getRegisteredWebhooks(): Record<string, WebhookRegistration[]> {
    const result: Record<string, WebhookRegistration[]> = {};

    for (const [url, registrations] of this.registeredWebhooks.entries()) {
      result[url] = [...registrations];
    }

    return result;
  }

  /**
   * Health check for webhook delivery capability
   */
  async healthCheck(): Promise<{ status: 'healthy' | 'unhealthy'; details?: any }> {
    try {
      // Check if we can make a basic network request
      const hasRegistrations = this.registeredWebhooks.size > 0;
      const circuitBreakerHealthy = !this.circuitBreaker ||
        this.circuitBreaker.getMetrics().state !== 'OPEN';

      return {
        status: hasRegistrations && circuitBreakerHealthy ? 'healthy' : 'unhealthy',
        details: {
          registeredWebhooks: this.registeredWebhooks.size,
          circuitBreakerState: this.circuitBreaker?.getMetrics().state,
          hasRegistrations
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: { error: error instanceof Error ? error.message : String(error) }
      };
    }
  }
}