/**
 * Marketplace resource — search, featured, reviews, leaderboard, stats
 */

import type { HttpRequester } from '../http-requester.js';
import type {
  Mission, Review, PublicStats,
  MarketplaceSearchParams, SubmitReviewParams, PaginatedResponse,
} from '../types.js';

export class MarketplaceResource {
  constructor(private readonly http: HttpRequester) {}

  search(params?: MarketplaceSearchParams): Promise<PaginatedResponse<Mission>> {
    return this.http.get('/marketplace', params as Record<string, string | number | undefined>);
  }

  getFeatured(): Promise<Mission[]> {
    return this.http.get('/marketplace/featured');
  }

  getStats(): Promise<PublicStats> {
    return this.http.get('/marketplace/stats');
  }

  getLeaderboard(): Promise<{ tenant_id: string; referrals: number; credits_earned: number }[]> {
    return this.http.get('/marketplace/leaderboard');
  }

  getReviews(missionId: string): Promise<Review[]> {
    return this.http.get(`/marketplace/${missionId}/reviews`);
  }

  submitReview(missionId: string, params: SubmitReviewParams): Promise<Review> {
    return this.http.post(`/marketplace/${missionId}/reviews`, params);
  }
}
