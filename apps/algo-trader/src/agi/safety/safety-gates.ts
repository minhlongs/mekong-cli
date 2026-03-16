// Confidence Gate - validates decision confidence before execution

export interface ConfidenceGateOptions {
  minConfidence: number; // e.g., 0.6 for 60% minimum
  reviewThreshold?: number; // e.g., 0.7 - below this needs human review
}

export class ConfidenceGate {
  private options: ConfidenceGateOptions;

  constructor(options: ConfidenceGateOptions) {
    this.options = options;
  }

  /**
   * Check if confidence meets threshold
   * Returns: 'approved' | 'needs_review' | 'rejected'
   */
  check(confidence: number): 'approved' | 'needs_review' | 'rejected' {
    if (confidence < this.options.minConfidence) {
      return 'rejected';
    }

    const reviewThreshold = this.options.reviewThreshold || this.options.minConfidence + 0.1;
    if (confidence < reviewThreshold) {
      return 'needs_review';
    }

    return 'approved';
  }

  /**
   * Validate and get result
   */
  validate(confidence: number): {
    approved: boolean;
    needsReview: boolean;
    reason?: string;
  } {
    const result = this.check(confidence);

    return {
      approved: result === 'approved',
      needsReview: result === 'needs_review',
      reason: result === 'rejected'
        ? `Confidence ${confidence.toFixed(2)} below minimum ${this.options.minConfidence}`
        : result === 'needs_review'
          ? `Confidence ${confidence.toFixed(2)} below review threshold`
          : undefined,
    };
  }
}

// Kill Switch - immediate stop all trading

// CONVENTION: isActive() === true means the kill switch is ACTIVE (TRIPPED),
// i.e., trading is BLOCKED. This matches circuit-breakers.ts KillSwitch.isActive().
// Do NOT call isActive() to check if trading is allowed — use !isActive() for that.

export type KillSwitchState = 'normal' | 'triggered';

export class KillSwitch {
  private state: KillSwitchState = 'normal';
  private triggeredAt: number | null = null;
  private triggeredBy: string | null = null;
  private reason: string | null = null;

  /**
   * Trigger kill switch — blocks all trading (isActive() will return true)
   */
  trigger(triggeredBy: string, reason: string): void {
    this.state = 'triggered';
    this.triggeredAt = Date.now();
    this.triggeredBy = triggeredBy;
    this.reason = reason;
    console.error(`[KillSwitch] TRIGGERED by ${triggeredBy}: ${reason}`);
  }

  /**
   * Reset kill switch — allows trading to resume (isActive() returns false)
   */
  reset(): void {
    this.state = 'normal';
    this.triggeredAt = null;
    this.triggeredBy = null;
    this.reason = null;
    console.log('[KillSwitch] Reset - trading can resume');
  }

  /**
   * Returns true when kill switch is ACTIVE (TRIPPED) — trading is BLOCKED.
   * Returns false when trading is allowed (normal state).
   * Convention matches circuit-breakers.ts KillSwitch.isActive().
   */
  isActive(): boolean {
    return this.state === 'triggered';
  }

  /**
   * Check if kill switch is triggered (trading blocked) — alias for isActive()
   */
  isTriggered(): boolean {
    return this.state === 'triggered';
  }

  /**
   * Get current state
   */
  getState(): {
    state: KillSwitchState;
    isActive: boolean;
    triggeredAt: number | null;
    triggeredBy: string | null;
    reason: string | null;
  } {
    return {
      state: this.state,
      isActive: this.isActive(),
      triggeredAt: this.triggeredAt,
      triggeredBy: this.triggeredBy,
      reason: this.reason,
    };
  }
}
