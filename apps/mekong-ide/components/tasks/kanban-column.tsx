"use client";

/**
 * KanbanColumn — single droppable column. Uses HTML5 drag-and-drop (no library).
 */

import { useState } from "react";
import { TaskCard } from "./task-card";
import type { Task, TaskStatus } from "@/lib/types/task-types";

interface KanbanColumnProps {
  status: TaskStatus;
  label: string;
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (task: Task) => void;
  onDragStart: (e: React.DragEvent, taskId: string) => void;
  onDrop: (e: React.DragEvent, targetStatus: TaskStatus) => void;
}

const columnAccent: Record<TaskStatus, string> = {
  todo: "var(--text-muted)",
  in_progress: "var(--status-warning)",
  done: "var(--status-success)",
};

export function KanbanColumn({
  status, label, tasks, selectedTaskId, onSelectTask, onDragStart, onDrop,
}: KanbanColumnProps) {
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { setDragOver(false); onDrop(e, status); }}
      style={{
        flex: 1,
        minWidth: 0,
        background: dragOver ? "var(--surface-hover)" : "var(--bg-secondary)",
        border: `1px solid ${dragOver ? "var(--accent-teal-500)" : "var(--border-subtle)"}`,
        borderRadius: "0.5rem",
        padding: "0.75rem",
        transition: "border-color 0.15s, background 0.15s",
        display: "flex",
        flexDirection: "column",
        minHeight: "400px",
      }}
    >
      {/* Column header */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <span style={{ width: "0.5rem", height: "0.5rem", borderRadius: "50%", background: columnAccent[status] }} />
        <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          {label}
        </span>
        <span style={{
          marginLeft: "auto",
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          background: "var(--surface-card)",
          padding: "0.0625rem 0.375rem",
          borderRadius: "9999px",
          border: "1px solid var(--border-subtle)",
        }}>
          {tasks.length}
        </span>
      </div>

      {/* Task list */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            isSelected={selectedTaskId === task.id}
            onClick={onSelectTask}
            onDragStart={onDragStart}
          />
        ))}
        {tasks.length === 0 && (
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textAlign: "center", paddingTop: "2rem" }}>
            Drop tasks here
          </div>
        )}
      </div>
    </div>
  );
}
