/**
 * Shared types for webhook simulator service
 */

export interface SimulationRow {
  id: string;
  tenant_id: string;
  target_url: string;
  event_type: string;
  payload: string;
  status: string;
  response_code: number | null;
  response_body: string | null;
  latency_ms: number | null;
  retry_count: number;
  created_at: string;
  completed_at: string | null;
}

export interface TestEndpointRow {
  id: string;
  tenant_id: string;
  endpoint_path: string;
  received_count: number;
  last_payload: string | null;
  last_received_at: string | null;
  created_at: string;
}

export interface DeliveryResult {
  code: number;
  body: string;
  latency: number;
}
