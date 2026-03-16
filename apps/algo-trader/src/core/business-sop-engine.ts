/**
 * Business SOP Engine — executable SOPs as algorithms.
 * Each SOP is a function that reads state, evaluates conditions, outputs decisions.
 * Not documentation — this is the actual decision engine.
 */

import { ProductionRiskGate } from './production-risk-gate';
import { TradeDecisionAuditLogger } from './trade-decision-audit-logger';
import { logger } from '../utils/logger';

// --- Types ---

export type AlertLevel = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
export type StrategyAction = 'PROMOTE' | 'KEEP' | 'DEMOTE' | 'KILL';
export type ScaleDecision = 'SCALE_UP' | 'HOLD' | 'SCALE_DOWN' | 'HALT';

export interface StrategyPerformance {
  name: string;
  sharpe: number;
  winRate: number;
  totalPnl: number;
  drawdownPct: number;
  tradeCount: number;
}

export interface SOPDecision {
  timestamp: number;
  sop: string;
  decision: string;
  reasoning: string;
  actions: string[];
}

// --- SOP 1: Daily Health Check (08:00) ---

export function sopDailyHealthCheck(riskGate: ProductionRiskGate): SOPDecision {
  const status = riskGate.getStatus();
  let level: AlertLevel = 'GREEN';
  const actions: string[] = [];

  if (status.anyTripped) {
    level = 'RED';
    actions.push('HALT all trading immediately');
    actions.push('Notify founder via Telegram');
  } else if (status.drawdownPct > 5) {
    level = 'ORANGE';
    actions.push('Reduce position sizes by 50%');
    actions.push('Review underperforming strategies');
  } else if (status.dailyPnl < 0) {
    level = 'YELLOW';
    actions.push('Monitor closely, no new positions until PnL turns positive');
  } else {
    actions.push('Continue normal operations');
  }

  return {
    timestamp: Date.now(),
    sop: 'DAILY_HEALTH_CHECK',
    decision: level,
    reasoning: `Portfolio $${status.portfolioValue.toFixed(0)} | Daily PnL $${status.dailyPnl.toFixed(0)} | Drawdown ${status.drawdownPct.toFixed(1)}% | Orders/min ${status.ordersThisMinute}`,
    actions,
  };
}

// --- SOP 2: Strategy Lifecycle (Weekly) ---

export function sopStrategyLifecycle(strategies: StrategyPerformance[]): SOPDecision {
  const actions: string[] = [];
  const decisions: Record<string, StrategyAction> = {};

  for (const s of strategies) {
    if (s.tradeCount < 20) {
      decisions[s.name] = 'KEEP'; // Not enough data
      continue;
    }

    if (s.sharpe >= 2.0 && s.winRate >= 0.6) {
      decisions[s.name] = 'PROMOTE';
      actions.push(`PROMOTE ${s.name}: Sharpe ${s.sharpe.toFixed(2)}, WR ${(s.winRate * 100).toFixed(0)}%`);
    } else if (s.sharpe < 0.5 || s.drawdownPct > 15) {
      decisions[s.name] = 'KILL';
      actions.push(`KILL ${s.name}: Sharpe ${s.sharpe.toFixed(2)}, DD ${s.drawdownPct.toFixed(1)}%`);
    } else if (s.sharpe < 1.0) {
      decisions[s.name] = 'DEMOTE';
      actions.push(`DEMOTE ${s.name}: reduce allocation 50%`);
    } else {
      decisions[s.name] = 'KEEP';
    }
  }

  return {
    timestamp: Date.now(),
    sop: 'STRATEGY_LIFECYCLE',
    decision: JSON.stringify(decisions),
    reasoning: `Evaluated ${strategies.length} strategies`,
    actions: actions.length > 0 ? actions : ['All strategies performing within bounds'],
  };
}

// --- SOP 3: Capital Scaling (Monthly) ---

export function sopCapitalScaling(
  currentCapital: number,
  monthlyReturn: number,
  maxDrawdown: number,
  consecutiveProfitableDays: number,
): SOPDecision {
  let decision: ScaleDecision;
  const actions: string[] = [];
  const monthlyReturnPct = (monthlyReturn / currentCapital) * 100;

  if (maxDrawdown > 10) {
    decision = 'HALT';
    actions.push(`HALT: Drawdown ${maxDrawdown.toFixed(1)}% > 10% threshold`);
    actions.push('Activate kill switch, review all strategies');
  } else if (monthlyReturnPct < 0) {
    decision = 'SCALE_DOWN';
    actions.push(`SCALE_DOWN 50%: Negative return ${monthlyReturnPct.toFixed(1)}%`);
  } else if (monthlyReturnPct > 10 && consecutiveProfitableDays >= 20 && maxDrawdown < 5) {
    decision = 'SCALE_UP';
    const nextTier = Math.min(currentCapital * 2, 500000);
    actions.push(`SCALE_UP to $${nextTier.toLocaleString()}: Return ${monthlyReturnPct.toFixed(1)}%, ${consecutiveProfitableDays} profitable days`);
  } else {
    decision = 'HOLD';
    actions.push(`HOLD at $${currentCapital.toLocaleString()}: Return ${monthlyReturnPct.toFixed(1)}%`);
  }

  return {
    timestamp: Date.now(),
    sop: 'CAPITAL_SCALING',
    decision,
    reasoning: `Capital $${currentCapital.toLocaleString()} | Return ${monthlyReturnPct.toFixed(1)}% | DD ${maxDrawdown.toFixed(1)}% | Streak ${consecutiveProfitableDays}d`,
    actions,
  };
}

// --- SOP 4: Emergency Protocol ---

export function sopEmergencyProtocol(
  riskGate: ProductionRiskGate,
  drawdownPct: number,
  dailyLossPct: number,
): SOPDecision {
  const actions: string[] = [];
  let level: AlertLevel;

  if (drawdownPct > 10 || dailyLossPct > 5) {
    level = 'RED';
    actions.push('KILL SWITCH: halt ALL trading');
    actions.push('Cancel all open orders');
    actions.push('Telegram alert to founder');
    actions.push('Generate incident report');
    riskGate.emergencyStop(`RED ALERT: DD=${drawdownPct.toFixed(1)}% DailyLoss=${dailyLossPct.toFixed(1)}%`);
  } else if (drawdownPct > 7 || dailyLossPct > 3) {
    level = 'ORANGE';
    actions.push('FREEZE: no new positions');
    actions.push('Reduce existing positions by 50%');
    actions.push('Alert CTO for review');
  } else if (drawdownPct > 5 || dailyLossPct > 2) {
    level = 'YELLOW';
    actions.push('CAUTION: tighten stop-losses to 10%');
    actions.push('Reduce Kelly fraction to quarter');
  } else {
    level = 'GREEN';
    actions.push('Normal operations');
  }

  return {
    timestamp: Date.now(),
    sop: 'EMERGENCY_PROTOCOL',
    decision: level,
    reasoning: `Drawdown ${drawdownPct.toFixed(1)}% | Daily loss ${dailyLossPct.toFixed(1)}%`,
    actions,
  };
}

// --- SOP Runner: Execute all SOPs and log decisions ---

export class SOPRunner {
  private riskGate: ProductionRiskGate;
  private auditLogger: TradeDecisionAuditLogger;
  private history: SOPDecision[] = [];

  constructor(riskGate: ProductionRiskGate, auditLogger: TradeDecisionAuditLogger) {
    this.riskGate = riskGate;
    this.auditLogger = auditLogger;
  }

  /** Run daily health check SOP */
  runDailyHealth(): SOPDecision {
    const decision = sopDailyHealthCheck(this.riskGate);
    this.record(decision);
    return decision;
  }

  /** Run strategy lifecycle SOP */
  runStrategyLifecycle(strategies: StrategyPerformance[]): SOPDecision {
    const decision = sopStrategyLifecycle(strategies);
    this.record(decision);
    return decision;
  }

  /** Run capital scaling SOP */
  runCapitalScaling(capital: number, monthlyReturn: number, maxDD: number, streak: number): SOPDecision {
    const decision = sopCapitalScaling(capital, monthlyReturn, maxDD, streak);
    this.record(decision);
    return decision;
  }

  /** Run emergency protocol SOP */
  runEmergency(drawdownPct: number, dailyLossPct: number): SOPDecision {
    const decision = sopEmergencyProtocol(this.riskGate, drawdownPct, dailyLossPct);
    this.record(decision);
    return decision;
  }

  /** Get all SOP decisions history */
  getHistory(): SOPDecision[] {
    return [...this.history];
  }

  private record(decision: SOPDecision): void {
    this.history.push(decision);
    logger.info(`[SOP] ${decision.sop}: ${decision.decision} — ${decision.actions[0]}`);
  }
}
