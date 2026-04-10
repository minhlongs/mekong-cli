/**
 * Task Tracker hook — full CRUD with optimistic drag-drop status changes.
 */
"use client";

import { useCallback } from "react";
import { useApi } from "./use-api";
import {
  listTasks,
  createTask,
  updateTask,
  deleteTask,
  type CreateTaskRequest,
  type UpdateTaskRequest,
} from "@/lib/api/endpoints/task-api";
import type { Task, TaskStatus } from "@/lib/types/task-types";
import { MOCK_TASKS } from "@/lib/mock/task-mock-data";

interface UseTasksResult {
  tasks: Task[] | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  create: (data: CreateTaskRequest) => Promise<void>;
  update: (id: string, data: UpdateTaskRequest) => Promise<void>;
  remove: (id: string) => Promise<void>;
  /** Drag-drop shortcut: change only the status field */
  moveToStatus: (id: string, status: TaskStatus) => Promise<void>;
  refetch: () => void;
}

export function useTasks(): UseTasksResult {
  const { data, isLoading, error, isDemoMode, refetch } = useApi<Task[]>(
    listTasks,
    MOCK_TASKS
  );

  const create = useCallback(async (req: CreateTaskRequest) => {
    if (isDemoMode) return;
    await createTask(req);
    refetch();
  }, [isDemoMode, refetch]);

  const update = useCallback(async (id: string, req: UpdateTaskRequest) => {
    if (isDemoMode) return;
    await updateTask(id, req);
    refetch();
  }, [isDemoMode, refetch]);

  const remove = useCallback(async (id: string) => {
    if (isDemoMode) return;
    await deleteTask(id);
    refetch();
  }, [isDemoMode, refetch]);

  const moveToStatus = useCallback(
    async (id: string, status: TaskStatus) => update(id, { status }),
    [update]
  );

  return { tasks: data, isLoading, error, isDemoMode, create, update, remove, moveToStatus, refetch };
}
