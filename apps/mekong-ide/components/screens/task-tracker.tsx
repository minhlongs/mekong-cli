"use client";

/**
 * TaskTrackerScreen — Screen 7 (1440x900): Kanban board + task detail panel.
 * Header with filter bar and "New Task" button.
 */

import { useState } from "react";
import { Button } from "@/components/ds";
import { KanbanBoard } from "@/components/tasks/kanban-board";
import { TaskDetailPanel } from "@/components/tasks/task-detail-panel";
import type { Task } from "@/lib/types/task-types";

type FilterMode = "all" | "mine" | "blocked";

export function TaskTrackerScreen() {
  const [filter, setFilter] = useState<FilterMode>("all");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const filters: { label: string; value: FilterMode }[] = [
    { label: "All", value: "all" },
    { label: "Mine", value: "mine" },
    { label: "Blocked", value: "blocked" },
  ];

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "var(--bg-primary)",
      fontFamily: "var(--font-mono, monospace)",
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "1rem",
        padding: "0.75rem 1.25rem",
        borderBottom: "1px solid var(--border-subtle)",
        background: "var(--bg-secondary)",
        flexShrink: 0,
      }}>
        <h1 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
          Task Tracker
        </h1>

        {/* Filter tabs */}
        <div style={{ display: "flex", gap: "0.25rem", background: "var(--surface-card)", borderRadius: "0.375rem", padding: "0.125rem", border: "1px solid var(--border-subtle)" }}>
          {filters.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              style={{
                padding: "0.25rem 0.75rem",
                fontSize: "0.75rem",
                fontWeight: 500,
                borderRadius: "0.25rem",
                cursor: "pointer",
                border: "none",
                background: filter === value ? "var(--accent-teal-500)" : "transparent",
                color: filter === value ? "#000" : "var(--text-secondary)",
                transition: "background 0.15s",
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ marginLeft: "auto" }}>
          <Button variant="primary" size="sm">+ New Task</Button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Kanban area */}
        <div style={{ flex: 1, padding: "0.875rem", overflow: "auto", display: "flex", flexDirection: "column" }}>
          <KanbanBoard
            filter={filter}
            selectedTaskId={selectedTask?.id ?? null}
            onSelectTask={setSelectedTask}
          />
        </div>

        {/* Detail panel */}
        <TaskDetailPanel task={selectedTask} />
      </div>
    </div>
  );
}
