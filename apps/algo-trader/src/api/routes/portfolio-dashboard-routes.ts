/**
 * Portfolio Dashboard API Routes — real-time portfolio status for dashboard.
 * GET /api/portfolio — full portfolio status + risk gate + audit stats
 * GET /api/portfolio/pnl-history — PnL time series for charting
 * GET /api/portfolio/audit — recent audit log entries
 */

import { FastifyInstance } from 'fastify';
import { ProductionRiskGate } from '../../core/production-risk-gate';
import { TradeDecisionAuditLogger } from '../../core/trade-decision-audit-logger';
import { PortfolioManager } from '../../core/PortfolioManager';

/** Register portfolio routes — pass instances from app bootstrap */
export function registerPortfolioDashboardRoutes(
  app: FastifyInstance,
  riskGate: ProductionRiskGate,
  auditLogger: TradeDecisionAuditLogger,
): void {
  // GET /api/portfolio — full status
  app.get('/api/portfolio', async (_req, reply) => {
    const riskStatus = riskGate.getStatus();
    const auditStats = auditLogger.getStats();
    const pm = PortfolioManager.getInstance();
    const summary = pm.getPortfolioSummary();

    return reply.send({
      status: 'ok',
      timestamp: Date.now(),
      portfolio: {
        value: riskStatus.portfolioValue,
        peakValue: riskStatus.peakValue,
        dailyPnl: riskStatus.dailyPnl,
        drawdownPct: riskStatus.drawdownPct,
        totalPnl: summary.totalPnl,
        realizedPnl: summary.realizedPnl,
        unrealizedPnl: summary.unrealizedPnl,
        openPositions: summary.totalPositions,
        closedPositions: 0,
      },
      risk: {
        anyTripped: riskStatus.anyTripped,
        killSwitch: riskStatus.killSwitch,
        dailyLoss: riskStatus.dailyLoss,
        drawdown: riskStatus.maxDrawdown,
        consecutiveLoss: riskStatus.consecutiveLoss,
        ordersThisMinute: riskStatus.ordersThisMinute,
      },
      audit: auditStats,
      config: riskStatus.config,
    });
  });

  // GET /api/portfolio/audit?limit=50
  app.get('/api/portfolio/audit', async (req, reply) => {
    const limit = parseInt((req.query as any)?.limit || '50', 10);
    const entries = auditLogger.getRecent(Math.min(limit, 500));
    return reply.send({ entries, total: auditLogger.getStats().total });
  });

  // GET /api/portfolio/positions
  app.get('/api/portfolio/positions', async (_req, reply) => {
    const pm = PortfolioManager.getInstance();
    const positions = pm.getOpenPositions();
    const exposures = pm.getMarketExposure();
    return reply.send({ positions, exposures, count: positions.length });
  });
}
