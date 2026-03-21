/**
 * Mission Service — Submit, track, and manage agent missions
 */

import type { Env } from '../index';
import { CreditService, MISSION_COSTS } from './credit-service';

export interface Mission {
  id: string;
  tenantId: string;
  goal: string;
  complexity: 'simple' | 'standard' | 'complex';
  status: 'queued' | 'planning' | 'executing' | 'verifying' | 'completed' | 'failed' | 'cancelled';
  creditsCost: number;
  project?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
}

export interface SubmitResult {
  success: boolean;
  mission?: Mission;
  error?: string;
  code?: string;
}

export class MissionService {
  private creditService: CreditService;

  constructor(private env: Env) {
    this.creditService = new CreditService(env);
  }

  /**
   * Submit a new mission — deducts credits atomically
   */
  async submit(
    tenantId: string,
    goal: string,
    complexity: 'simple' | 'standard' | 'complex' = 'standard',
    project?: string
  ): Promise<SubmitResult> {
    const cost = MISSION_COSTS[complexity] || MISSION_COSTS.standard;

    // Deduct credits first (atomic — prevents overdraw)
    const deductResult = await this.creditService.deduct(
      tenantId, cost, 'mission', `Mission: ${goal.slice(0, 100)}`
    );

    if (!deductResult.success) {
      return {
        success: false,
        error: deductResult.error === 'INSUFFICIENT_CREDITS'
          ? `Insufficient credits. Need ${cost}, have ${deductResult.balance ?? 0}`
          : 'Tenant not found',
        code: deductResult.error,
      };
    }

    // Create mission record
    const missionId = crypto.randomUUID();
    const now = new Date().toISOString();

    await this.env.DB.prepare(
      `INSERT INTO missions (id, tenant_id, goal, complexity, status, credits_cost, project, created_at)
       VALUES (?, ?, ?, ?, 'queued', ?, ?, ?)`
    )
      .bind(missionId, tenantId, goal, complexity, cost, project || null, now)
      .run();

    return {
      success: true,
      mission: {
        id: missionId,
        tenantId,
        goal,
        complexity,
        status: 'queued',
        creditsCost: cost,
        project,
        createdAt: now,
      },
    };
  }

  /**
   * Get mission by ID (with tenant ownership check)
   */
  async get(missionId: string, tenantId: string): Promise<Mission | null> {
    const result = await this.env.DB.prepare(
      `SELECT id, tenant_id as tenantId, goal, complexity, status,
              credits_cost as creditsCost, project, created_at as createdAt,
              started_at as startedAt, completed_at as completedAt,
              error_message as errorMessage
       FROM missions WHERE id = ? AND tenant_id = ?`
    )
      .bind(missionId, tenantId)
      .first<Mission>();

    return result || null;
  }

  /**
   * List missions for a tenant
   */
  async list(
    tenantId: string,
    options: { status?: string; limit?: number; offset?: number } = {}
  ): Promise<{ missions: Mission[]; total: number }> {
    const limit = Math.min(Math.max(options.limit || 20, 1), 100);
    const offset = Math.max(options.offset || 0, 0);

    let query = `SELECT id, tenant_id as tenantId, goal, complexity, status,
                        credits_cost as creditsCost, project, created_at as createdAt,
                        started_at as startedAt, completed_at as completedAt,
                        error_message as errorMessage
                 FROM missions WHERE tenant_id = ?`;
    let countQuery = 'SELECT COUNT(*) as total FROM missions WHERE tenant_id = ?';
    const bindings: unknown[] = [tenantId];
    const countBindings: unknown[] = [tenantId];

    if (options.status) {
      query += ' AND status = ?';
      countQuery += ' AND status = ?';
      bindings.push(options.status);
      countBindings.push(options.status);
    }

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
    bindings.push(limit, offset);

    const [results, countResult] = await Promise.all([
      this.env.DB.prepare(query).bind(...bindings).all<Mission>(),
      this.env.DB.prepare(countQuery).bind(...countBindings).first<{ total: number }>(),
    ]);

    return {
      missions: results.results,
      total: countResult?.total ?? 0,
    };
  }

  /**
   * Cancel a queued mission and refund credits
   */
  async cancel(missionId: string, tenantId: string): Promise<{ success: boolean; error?: string }> {
    const mission = await this.get(missionId, tenantId);

    if (!mission) {
      return { success: false, error: 'Mission not found' };
    }

    if (mission.status !== 'queued') {
      return { success: false, error: `Cannot cancel mission in ${mission.status} status` };
    }

    // Update status
    await this.env.DB.prepare(
      "UPDATE missions SET status = 'cancelled', completed_at = ? WHERE id = ? AND tenant_id = ?"
    )
      .bind(new Date().toISOString(), missionId, tenantId)
      .run();

    // Refund credits
    await this.creditService.addCredits(
      tenantId,
      mission.creditsCost,
      'refund',
      `Cancelled mission: ${mission.goal.slice(0, 80)}`,
      { mission_id: missionId }
    );

    return { success: true };
  }
}
