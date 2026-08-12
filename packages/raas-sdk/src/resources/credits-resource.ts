/**
 * Credits resource — balance, history, check cost, redeem, feedback
 */

import type { HttpRequester } from '../http-requester.js';
import type {
  CreditTransaction,
  CreditCheckParams, CreditCheckResponse,
  RedeemCouponParams, SubmitFeedbackParams,
} from '../types.js';

export class CreditsResource {
  constructor(private readonly http: HttpRequester) {}

  getBalance(): Promise<{ balance: number; total_spent: number }> {
    return this.http.get('/credits');
  }

  /** Pre-check cost before submitting a mission */
  check(params: CreditCheckParams): Promise<CreditCheckResponse> {
    return this.http.post('/credits/check', params);
  }

  getHistory(): Promise<CreditTransaction[]> {
    return this.http.get('/credits/history');
  }

  redeem(params: RedeemCouponParams): Promise<{ credited: number; balance: number }> {
    return this.http.post('/v1/credits/redeem', params);
  }

  submitFeedback(params: SubmitFeedbackParams): Promise<{ success: boolean }> {
    return this.http.post('/v1/credits/feedback', params);
  }
}
