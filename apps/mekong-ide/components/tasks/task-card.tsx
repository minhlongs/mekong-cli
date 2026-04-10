"use client";

/**
 * TaskCard — draggable kanban card showing title, priority badge, owner, MCU cost.
 */

import { Badge } from "@/components/ds";
import type { BadgeVariant } from "@/lib/types";
import type { Task, TaskPriority } from "@/lib/types/task-types";

interface TaskCardProps {
  task: Task;
  isSelected: boolean;
  onClick: (task: Task) => void;
  onDragStart: (e: React.DragEvent, taskId: string) => void;
}

const priorityVariant: Record<TaskPriority, BadgeVariant> = {
  low: "info",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

export function TaskCard({ task, isSelected, onClick, onDragStart }: TaskCardProps) {
  const depCount = task.blockedBy.length;

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, task.id)}
      onClick={() => onClick(task)}
      style={{
        background: isSelected ? "var(--surface-hover)" : "var(--surface-card)",
        border: `1px solid ${isSelected ? "var(--accent-teal-500)" : "var(--border-subtle)"}`,
        borderRadius: "0.5rem",
        padding: "0.75rem",
        cursor: "grab",
        userSelect: "none",
        transition: "border-color 0.15s, background 0.15s",
        marginBottom: "0.5rem",
      }}
      onMouseEnter={(e) => {
        if (!isSelected) (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-strong)";
      }}
      onMouseLeave={(e) => {
        if (!isSelected) (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-subtle)";
      }}
    >
      <div style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
        {task.title}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        <Badge variant={priorityVariant[task.priority]} label={task.priority} />
        <span style={{
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          background: "var(--bg-secondary)",
          padding: "0.125rem 0.375rem",
          borderRadius: "0.25rem",
        }}>
          @{task.owner}
        </span>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "auto" }}>
          {task.mcuCost} MCU
        </span>
      </div>
      {depCount > 0 && (
        <div style={{ marginTop: "0.375rem", fontSize: "0.75rem", color: "var(--status-warning)" }}>
          {depCount} dep{depCount > 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
