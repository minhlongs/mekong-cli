/**
 * Missions resource — submit, poll, batch, share, templates
 */

import type { HttpRequester } from '../http-requester.js';
import type {
  Mission, MissionPoll, Template,
  SubmitMissionParams, ListMissionsParams, BatchSubmitParams,
  PaginatedResponse,
} from '../types.js';

export class MissionsResource {
  constructor(private readonly http: HttpRequester) {}

  submit(params: SubmitMissionParams): Promise<Mission> {
    return this.http.post('/v1/missions', params);
  }

  get(id: string): Promise<Mission> {
    return this.http.get(`/v1/missions/${id}`);
  }

  list(params?: ListMissionsParams): Promise<PaginatedResponse<Mission>> {
    return this.http.get('/v1/missions', params as Record<string, string | number | undefined>);
  }

  poll(id: string): Promise<MissionPoll> {
    return this.http.get(`/v1/missions/${id}/poll`);
  }

  cancel(id: string): Promise<{ success: boolean; refunded: number }> {
    return this.http.post(`/v1/missions/${id}/cancel`);
  }

  share(id: string): Promise<{ share_url: string }> {
    return this.http.post(`/v1/missions/${id}/share`);
  }

  batch(params: BatchSubmitParams): Promise<Mission[]> {
    return this.http.post('/v1/missions/batch', params);
  }

  listTemplates(category?: string): Promise<Template[]> {
    return this.http.get('/v1/missions/templates', category ? { category } : undefined);
  }
}
