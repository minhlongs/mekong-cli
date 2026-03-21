/**
 * API Server
 * REST + WebSocket gateway for trading operations
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

import { tradesRouter } from './routes/trades';
import { pnlRouter } from './routes/pnl';
import { signalsRouter } from './routes/signals';
import { adminRouter } from './routes/admin';
import { healthRouter } from './routes/health';
import { revenueRouter } from './routes/revenue';
import { metricsMiddleware, getMetrics } from '../middleware/prometheus-metrics';
import { errorHandler } from '../middleware/error-handler';

export interface ApiConfig {
  port: number;
  corsOrigin: string | string[];
  rateLimitWindowMs: number;
  rateLimitMax: number;
}

export class ApiServer {
  private app: express.Application;
  private config: ApiConfig;
  private server?: any;

  constructor(config?: Partial<ApiConfig>) {
    this.app = express();
    this.config = {
      port: parseInt(process.env.API_PORT || '3000'),
      corsOrigin: process.env.CORS_ORIGIN || '*',
      rateLimitWindowMs: 60000, // 1 minute
      rateLimitMax: 100, // 100 requests per minute
      ...config,
    };

    this.setupMiddleware();
    this.setupRoutes();
  }

  /**
   * Setup middleware
   */
  private setupMiddleware(): void {
    // Security
    this.app.use(helmet());
    this.app.use(cors({ origin: this.config.corsOrigin }));

    // Body parsing
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Prometheus metrics middleware (track all requests)
    this.app.use(metricsMiddleware);

    // Rate limiting
    const limiter = rateLimit({
      windowMs: this.config.rateLimitWindowMs,
      max: this.config.rateLimitMax,
      message: { error: 'Too many requests, please try again later' },
    });
    this.app.use('/api', limiter);
  }

  /**
   * Setup routes
   */
  private setupRoutes(): void {
    // Health checks (no rate limit)
    this.app.use('/health', healthRouter);

    // Prometheus metrics endpoint (excluded from rate limiting)
    this.app.get('/metrics', getMetrics);

    // API routes
    this.app.use('/api/trades', tradesRouter);
    this.app.use('/api/pnl', pnlRouter);
    this.app.use('/api/signals', signalsRouter);
    this.app.use('/api/admin', adminRouter);
    this.app.use('/api/revenue', revenueRouter);

    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({ error: 'Not found' });
    });

    // Global error handler
    this.app.use(errorHandler);
  }

  /**
   * Start server
   */
  async start(): Promise<void> {
    return new Promise((resolve) => {
      this.server = this.app.listen(this.config.port, () => {
        console.log(`[ApiServer] Listening on port ${this.config.port}`);
        resolve();
      });
    });
  }

  /**
   * Stop server
   */
  async stop(): Promise<void> {
    if (this.server) {
      return new Promise((resolve) => {
        this.server.close(() => {
          console.log('[ApiServer] Stopped');
          resolve();
        });
      });
    }
  }

  /**
   * Get Express app (for testing)
   */
  getApp(): express.Application {
    return this.app;
  }
}
