"use client";

/**
 * TaskDetailPanel — 380px right panel: task info, dependencies list, session history, DAG toggle.
 */

import { useState } from "react";
import { Badge } from "@/components/ds";
import { DependencyDag } from "./dependency-dag";
import { MOCK_SESSION_HISTORY, MOCK_TASKS } from "@/lib/mock/task-mock-data";
import type { Task } from "@/lib/types/task-types";
import type { BadgeVariant } from "@/lib/types";

interface TaskDetailPanelProps {
  task: Task | null;
}

const statusBadge: Record<string, BadgeVariant> = {
  todo: "info",
  in_progress: "warning",
  done: "success",
};

const priorityBadge: Record<string, BadgeVariant> = {
  low: "info",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

export function TaskDetailPanel({ task }: TaskDetailPanelProps) {
  const [showDag, setShowDag] = useState(false);

  if (!task) {
    return (
      <div style={{
        width: 380, flexShrink: 0, borderLeft: "1px solid var(--border-subtle)",
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "var(--text-muted)", fontSize: "0.875rem", padding: "1.5rem",
      }}>
        Select a task to view details
      </div>
    );
  }

  const taskHistory = MOCK_SESSION_HISTORY.filter((h) => h.taskId === task.id);
  const allTasks = MOCK_TASKS;
  const blockedByTasks = allTasks.filter((t) => task.blockedBy.includes(t.id));
  const blocksTasks = allTasks.filter((t) => task.blocks.includes(t.id));

  return (
    <div style={{
      width: 380, flexShrink: 0, borderLeft: "1px solid var(--border-subtle)",
      display: "flex", flexDirection: "column", overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{ padding: "0.875rem 1rem", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
          {task.title}
        </div>
        <div style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}>
          <Badge variant={statusBadge[task.status]} label={task.status.replace("_", " ")} />
          <Badge variant={priorityBadge[task.priority]} label={task.priority} />
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "auto" }}>
            {task.mcuCost} MCU
          </span>
        </div>
      </div>

      {/* Body (scrollable) */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0.875rem 1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        {/* Description */}
        <section>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.375rem" }}>
            Description
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
            {task.description}
          </p>
        </section>

        {/* Owner */}
        <section>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.375rem" }}>
            Assignee
          </div>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>@{task.owner}</span>
        </section>

        {/* Blocked by */}
        {blockedByTasks.length > 0 && (
          <section>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.375rem" }}>
              Blocked by
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              {blockedByTasks.map((t) => (
                <span key={t.id} style={{ fontSize: "0.8125rem", color: "var(--status-warning)" }}>
                  ↑ {t.title}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Blocks */}
        {blocksTasks.length > 0 && (
          <section>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.375rem" }}>
              Blocks
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              {blocksTasks.map((t) => (
                <span key={t.id} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                  ↓ {t.title}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* DAG toggle */}
        <section>
          <button
            onClick={() => setShowDag((v) => !v)}
            style={{
              fontSize: "0.75rem", color: "var(--accent-teal-500)", background: "none",
              border: "none", cursor: "pointer", padding: 0, marginBottom: "0.5rem",
            }}
          >
            {showDag ? "Hide" : "Show"} dependency DAG
          </button>
          {showDag && (
            <div style={{ border: "1px solid var(--border-subtle)", borderRadius: "0.5rem", padding: "0.5rem", background: "var(--bg-secondary)" }}>
              <DependencyDag tasks={allTasks} focusTaskId={task.id} />
            </div>
          )}
        </section>

        {/* Session history */}
        <section>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.375rem" }}>
            Session History
          </div>
          {taskHistory.length === 0 ? (
            <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>No history yet</span>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
              {taskHistory.map((h, i) => (
                <div key={i} style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                  <span style={{ color: "var(--text-muted)", marginRight: "0.5rem" }}>
                    {new Date(h.timestamp).toLocaleTimeString()}
                  </span>
                  {h.action} <span style={{ color: "var(--text-muted)" }}>by @{h.agent}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
