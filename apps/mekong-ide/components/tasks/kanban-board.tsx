"use client";

/**
 * KanbanBoard — three-column kanban with HTML5 drag-and-drop state management.
 */

import { useState } from "react";
import { KanbanColumn } from "./kanban-column";
import { MOCK_TASKS } from "@/lib/mock/task-mock-data";
import type { Task, TaskStatus } from "@/lib/types/task-types";

interface KanbanBoardProps {
  filter: "all" | "mine" | "blocked";
  selectedTaskId: string | null;
  onSelectTask: (task: Task) => void;
}

const COLUMNS: { status: TaskStatus; label: string }[] = [
  { status: "todo", label: "To Do" },
  { status: "in_progress", label: "In Progress" },
  { status: "done", label: "Done" },
];

export function KanbanBoard({ filter, selectedTaskId, onSelectTask }: KanbanBoardProps) {
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS);
  const [draggingId, setDraggingId] = useState<string | null>(null);

  const filteredTasks = tasks.filter((t) => {
    if (filter === "mine") return t.owner === "frontend";
    if (filter === "blocked") return t.blockedBy.length > 0;
    return true;
  });

  function handleDragStart(e: React.DragEvent, taskId: string) {
    setDraggingId(taskId);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("taskId", taskId);
  }

  function handleDrop(e: React.DragEvent, targetStatus: TaskStatus) {
    e.preventDefault();
    const taskId = e.dataTransfer.getData("taskId") || draggingId;
    if (!taskId) return;
    setTasks((prev) =>
      prev.map((t) => t.id === taskId ? { ...t, status: targetStatus, updatedAt: new Date().toISOString() } : t)
    );
    setDraggingId(null);
  }

  return (
    <div style={{ display: "flex", gap: "0.75rem", flex: 1, minHeight: 0 }}>
      {COLUMNS.map(({ status, label }) => (
        <KanbanColumn
          key={status}
          status={status}
          label={label}
          tasks={filteredTasks.filter((t) => t.status === status)}
          selectedTaskId={selectedTaskId}
          onSelectTask={onSelectTask}
          onDragStart={handleDragStart}
          onDrop={handleDrop}
        />
      ))}
    </div>
  );
}
