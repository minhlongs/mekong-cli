/**
 * Task Tracker endpoint functions.
 * CRUD /v1/tasks, PATCH /v1/tasks/:id/status
 */

import { apiClient } from "../api-client";
import type { Task, TaskStatus, ApiResult } from "../api-types";

export interface CreateTaskRequest {
  title: string;
  description?: string;
  priority?: Task["priority"];
  owner?: string;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  priority?: Task["priority"];
  owner?: string;
  status?: TaskStatus;
}

export function listTasks(): Promise<ApiResult<Task[]>> {
  return apiClient.get<Task[]>("/v1/tasks");
}

export function createTask(data: CreateTaskRequest): Promise<ApiResult<Task>> {
  return apiClient.post<Task>("/v1/tasks", data);
}

export function updateTask(id: string, data: UpdateTaskRequest): Promise<ApiResult<Task>> {
  return apiClient.patch<Task>(`/v1/tasks/${id}`, data);
}

export function deleteTask(id: string): Promise<ApiResult<void>> {
  return apiClient.delete<void>(`/v1/tasks/${id}`);
}
