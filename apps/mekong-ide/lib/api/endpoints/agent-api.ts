/**
 * Agent / chat endpoint functions.
 * POST /v1/chat, GET /v1/models, GET /v1/pipeline/:sessionId
 */

import { apiClient } from "../api-client";
import type { ChatMessage, ModelConfig, PipelineStep, ApiResult } from "../api-types";

export interface SendMessageRequest {
  content: string;
  sessionId?: string;
  model?: string;
}

export interface SendMessageResponse {
  message: ChatMessage;
  sessionId: string;
}

export interface PipelineResponse {
  sessionId: string;
  steps: PipelineStep[];
}

export function sendMessage(
  req: SendMessageRequest
): Promise<ApiResult<SendMessageResponse>> {
  return apiClient.post<SendMessageResponse>("/v1/chat", req);
}

export function getModels(): Promise<ApiResult<ModelConfig[]>> {
  return apiClient.get<ModelConfig[]>("/v1/models");
}

export function getPipeline(sessionId: string): Promise<ApiResult<PipelineResponse>> {
  return apiClient.get<PipelineResponse>(`/v1/pipeline/${sessionId}`);
}
