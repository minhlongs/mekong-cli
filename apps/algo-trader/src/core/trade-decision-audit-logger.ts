/**
 * Trade Decision Audit Logger — logs every trade decision with reasoning
 * to audit-log.json for compliance and post-mortem analysis.
 * Append-only, rotates at 10K entries.
 */

import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../utils/logger';

export interface AuditEntry {
  id: string;
  timestamp: number;
  action: 'BUY' | 'SELL' | 'CANCEL' | 'REJECT';
  tokenId: string;
  marketId: string;
  side: 'YES' | 'NO';
  price: number;
  size: number;
  notional: number;
  /** Why this decision was made */
  reasoning: string;
  /** Strategy that generated the signal */
  strategy: string;
  /** Risk gate result */
  riskCheck: { allowed: boolean; reason?: string };
  /** Signal confidence */
  confidence: number;
  /** Kelly-recommended size (if applicable) */
  kellySizeUsd?: number;
  /** Paper or live */
  mode: 'LIVE' | 'PAPER' | 'DRY_RUN';
}

const AUDIT_LOG_PATH = path.resolve(process.cwd(), 'data', 'audit-log.json');
const MAX_ENTRIES = 10000;

export class TradeDecisionAuditLogger {
  private entries: AuditEntry[] = [];
  private entryCounter = 0;

  constructor() {
    this.load();
  }

  /** Log a trade decision */
  log(entry: Omit<AuditEntry, 'id' | 'timestamp'>): void {
    const full: AuditEntry = {
      ...entry,
      id: `audit_${++this.entryCounter}_${Date.now()}`,
      timestamp: Date.now(),
    };

    this.entries.push(full);

    // Rotate: keep last MAX_ENTRIES
    if (this.entries.length > MAX_ENTRIES) {
      this.entries = this.entries.slice(-MAX_ENTRIES);
    }

    this.save();
    logger.debug(`[Audit] ${full.action} ${full.side} ${full.size}@${full.price} — ${full.reasoning}`);
  }

  /** Get recent entries */
  getRecent(count: number = 50): AuditEntry[] {
    return this.entries.slice(-count);
  }

  /** Get entries by token */
  getByToken(tokenId: string): AuditEntry[] {
    return this.entries.filter(e => e.tokenId === tokenId);
  }

  /** Get summary stats */
  getStats(): { total: number; buys: number; sells: number; rejects: number; liveCount: number } {
    return {
      total: this.entries.length,
      buys: this.entries.filter(e => e.action === 'BUY').length,
      sells: this.entries.filter(e => e.action === 'SELL').length,
      rejects: this.entries.filter(e => e.action === 'REJECT').length,
      liveCount: this.entries.filter(e => e.mode === 'LIVE').length,
    };
  }

  /** Get all entries (for API) */
  getAll(): AuditEntry[] {
    return [...this.entries];
  }

  private save(): void {
    try {
      const dir = path.dirname(AUDIT_LOG_PATH);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(AUDIT_LOG_PATH, JSON.stringify(this.entries.slice(-MAX_ENTRIES), null, 2));
    } catch (err) {
      logger.warn('[Audit] Save failed:', err instanceof Error ? err.message : String(err));
    }
  }

  private load(): void {
    try {
      if (fs.existsSync(AUDIT_LOG_PATH)) {
        this.entries = JSON.parse(fs.readFileSync(AUDIT_LOG_PATH, 'utf8'));
        this.entryCounter = this.entries.length;
      }
    } catch {
      this.entries = [];
    }
  }
}
