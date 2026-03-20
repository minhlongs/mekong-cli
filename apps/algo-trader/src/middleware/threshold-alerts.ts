/**
 * Threshold Alerts
 * ROIaaS Phase 4 - Threshold alert events for usage monitoring
 */

import { EventEmitter } from 'events';
import { UsageMeteringService, ThresholdAlert } from '../metering/usage-metering-service';

export interface AlertHandler {
  (alert: ThresholdAlert): Promise<void> | void;
}

export interface AlertNotification {
  licenseKey: string;
  threshold: number;
  currentUsage: number;
  dailyLimit: number;
  percentUsed: number;
  timestamp: string;
  action?: string;
}

export class ThresholdAlerts extends EventEmitter {
  private static instance: ThresholdAlerts;
  private handlers: Map<number, AlertHandler[]> = new Map();

  private constructor() {
    super();
    this.setupDefaultHandlers();
  }

  static getInstance(): ThresholdAlerts {
    if (!ThresholdAlerts.instance) {
      ThresholdAlerts.instance = new ThresholdAlerts();
    }
    return ThresholdAlerts.instance;
  }

  private setupDefaultHandlers(): void {
    const meteringService = UsageMeteringService.getInstance();

    meteringService.on('threshold_alert', (alert: ThresholdAlert) => {
      this.emit('alert', alert);

      const handlers = this.handlers.get(alert.threshold) || [];
      for (const handler of handlers) {
        try {
          handler(alert);
        } catch (error) {
          console.error('Alert handler error:', error);
        }
      }
    });
  }

  onThreshold(threshold: number, handler: AlertHandler): void {
    if (!this.handlers.has(threshold)) {
      this.handlers.set(threshold, []);
    }
    this.handlers.get(threshold)!.push(handler);
  }

  onEightyPercent(handler: AlertHandler): void {
    this.onThreshold(80, handler);
  }

  onNinetyPercent(handler: AlertHandler): void {
    this.onThreshold(90, handler);
  }

  onHundredPercent(handler: AlertHandler): void {
    this.onThreshold(100, handler);
  }

  createNotification(alert: ThresholdAlert): AlertNotification {
    const notification: AlertNotification = {
      licenseKey: alert.licenseKey,
      threshold: alert.threshold,
      currentUsage: alert.currentUsage,
      dailyLimit: alert.dailyLimit,
      percentUsed: alert.percentUsed,
      timestamp: alert.timestamp,
    };

    if (alert.threshold === 80) {
      notification.action = 'warn';
    } else if (alert.threshold === 90) {
      notification.action = 'urgent';
    } else if (alert.threshold === 100) {
      notification.action = 'critical';
    }

    return notification;
  }

  async sendEmailNotification(
    alert: ThresholdAlert,
    sendFn: (to: string, subject: string, body: string) => Promise<void>,
    recipient: string
  ): Promise<void> {
    const notification = this.createNotification(alert);
    const subject = `Usage Alert: ${alert.threshold}% threshold reached`;
    const body = this.generateEmailBody(notification);

    await sendFn(recipient, subject, body);
  }

  async sendSmsNotification(
    alert: ThresholdAlert,
    sendFn: (to: string, message: string) => Promise<void>,
    recipient: string
  ): Promise<void> {
    const notification = this.createNotification(alert);
    const message = this.generateSmsBody(notification);

    await sendFn(recipient, message);
  }

  private generateEmailBody(notification: AlertNotification): string {
    const urgency = notification.action?.toUpperCase() || 'INFO';

    return `
USAGE THRESHOLD ALERT [${urgency}]

License Key: ${notification.licenseKey}
Threshold Reached: ${notification.threshold}%
Current Usage: ${notification.currentUsage.toLocaleString()} calls
Daily Limit: ${notification.dailyLimit.toLocaleString()} calls
Percent Used: ${notification.percentUsed.toFixed(1)}%
Time: ${notification.timestamp}

${this.getActionMessage(notification)}

Please review your usage and consider upgrading your tier if needed.
    `.trim();
  }

  private generateSmsBody(notification: AlertNotification): string {
    return `USAGE ALERT: ${notification.threshold}% reached. ${notification.currentUsage}/${notification.dailyLimit} calls. ${notification.action?.toUpperCase()}`;
  }

  private getActionMessage(notification: AlertNotification): string {
    switch (notification.action) {
      case 'warn':
        return 'Your usage is approaching the daily limit.';
      case 'urgent':
        return 'Your usage is near the daily limit. Overage charges may apply.';
      case 'critical':
        return 'You have reached or exceeded your daily limit. Overage charges are being applied.';
      default:
        return 'Please review your usage.';
    }
  }

  logAlert(alert: ThresholdAlert): void {
    const notification = this.createNotification(alert);
    console.log('[THRESHOLD ALERT]', JSON.stringify(notification, null, 2));
  }
}

export const thresholdAlerts = ThresholdAlerts.getInstance();
