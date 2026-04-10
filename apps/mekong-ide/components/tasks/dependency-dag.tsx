"use client";

/**
 * DependencyDag — SVG DAG visualizing task dependencies (topological left-to-right layout).
 */

import type { Task } from "@/lib/types/task-types";

interface DependencyDagProps {
  tasks: Task[];
  focusTaskId: string;
}

const NODE_W = 120;
const NODE_H = 36;
const COL_GAP = 60;
const ROW_GAP = 50;

/** Assign topological column level to each node */
function buildLevels(tasks: Task[], taskMap: Map<string, Task>): Map<string, number> {
  const levels = new Map<string, number>();

  function getLevel(id: string, visited: Set<string>): number {
    if (levels.has(id)) return levels.get(id)!;
    if (visited.has(id)) return 0;
    visited.add(id);
    const task = taskMap.get(id);
    if (!task || task.blockedBy.length === 0) {
      levels.set(id, 0);
      return 0;
    }
    const maxParent = Math.max(...task.blockedBy.map((pid) => getLevel(pid, visited)));
    const level = maxParent + 1;
    levels.set(id, level);
    return level;
  }

  tasks.forEach((t) => getLevel(t.id, new Set()));
  return levels;
}

const statusColor: Record<string, string> = {
  todo: "var(--text-muted)",
  in_progress: "var(--status-warning)",
  done: "var(--status-success)",
};

export function DependencyDag({ tasks, focusTaskId }: DependencyDagProps) {
  if (tasks.length === 0) return null;

  const taskMap = new Map(tasks.map((t) => [t.id, t]));
  const levels = buildLevels(tasks, taskMap);
  const maxLevel = Math.max(...Array.from(levels.values()));

  // Group by level, assign row within level
  const byLevel = new Map<number, string[]>();
  levels.forEach((lvl, id) => {
    if (!byLevel.has(lvl)) byLevel.set(lvl, []);
    byLevel.get(lvl)!.push(id);
  });

  // Compute node positions
  const positions = new Map<string, { x: number; y: number }>();
  byLevel.forEach((ids, lvl) => {
    ids.forEach((id, rowIdx) => {
      positions.set(id, {
        x: lvl * (NODE_W + COL_GAP) + 8,
        y: rowIdx * (NODE_H + ROW_GAP) + 8,
      });
    });
  });

  const maxRows = Math.max(...Array.from(byLevel.values()).map((v) => v.length));
  const svgW = (maxLevel + 1) * (NODE_W + COL_GAP) + 16;
  const svgH = maxRows * (NODE_H + ROW_GAP) + 16;

  // Build edges
  const edges: { from: string; to: string }[] = [];
  tasks.forEach((t) => {
    t.blockedBy.forEach((pid) => {
      if (taskMap.has(pid)) edges.push({ from: pid, to: t.id });
    });
  });

  return (
    <div style={{ overflowX: "auto", overflowY: "hidden" }}>
      <svg width={svgW} height={svgH} style={{ display: "block" }}>
        {/* Edges */}
        {edges.map(({ from, to }) => {
          const fp = positions.get(from);
          const tp = positions.get(to);
          if (!fp || !tp) return null;
          const x1 = fp.x + NODE_W;
          const y1 = fp.y + NODE_H / 2;
          const x2 = tp.x;
          const y2 = tp.y + NODE_H / 2;
          const cx = (x1 + x2) / 2;
          return (
            <path
              key={`${from}-${to}`}
              d={`M${x1},${y1} C${cx},${y1} ${cx},${y2} ${x2},${y2}`}
              fill="none"
              stroke="var(--border-strong)"
              strokeWidth={1.5}
              markerEnd="url(#arrow)"
            />
          );
        })}
        {/* Arrow marker */}
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 Z" fill="var(--border-strong)" />
          </marker>
        </defs>
        {/* Nodes */}
        {tasks.map((task) => {
          const pos = positions.get(task.id);
          if (!pos) return null;
          const isFocus = task.id === focusTaskId;
          return (
            <g key={task.id} transform={`translate(${pos.x},${pos.y})`}>
              <rect
                width={NODE_W} height={NODE_H} rx={6}
                fill={isFocus ? "var(--accent-teal-500)" : "var(--surface-card)"}
                stroke={isFocus ? "var(--accent-teal-500)" : statusColor[task.status] || "var(--border-subtle)"}
                strokeWidth={isFocus ? 2 : 1}
              />
              <text
                x={NODE_W / 2} y={NODE_H / 2}
                textAnchor="middle" dominantBaseline="middle"
                fontSize={10} fill={isFocus ? "#000" : "var(--text-primary)"}
                style={{ pointerEvents: "none" }}
              >
                {task.title.length > 16 ? task.title.slice(0, 15) + "…" : task.title}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
