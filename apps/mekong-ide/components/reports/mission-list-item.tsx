/**
 * Single mission row — displays goal text, status badge, timestamp, MCU cost.
 * Click navigates to the full report at /reports/{dept}/{command}/{missionId}.
 */
"use client";

import type React from "react";
import { useRouter } from "next/navigation";
import { Badge } from "@/components/ds";
import type { BadgeVariant } from "@/lib/types";
import type { MissionResult } from "@/lib/types/report-types";

interface MissionListItemProps {
  mission: MissionResult;
  department: string;
}

/** Map mission status → DS badge variant */
function statusVariant(status: MissionResult["status"]): BadgeVariant {
  switch (status) {
    case "success":  return "success";
    case "running":  return "info";
    case "error":    return "danger";
    case "pending":  return "warning";
    default:         return "info";
  }
}

function statusLabel(status: MissionResult["status"]): string {
  switch (status) {
    case "success": return "Completed";
    case "running": return "Running";
    case "error":   return "Failed";
    case "pending": return "Pending";
    default:        return status;
  }
}

/** Format ISO timestamp as relative human-readable string */
function relativeTime(iso: string): string {
  const delta = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(delta / 60_000);
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function MissionListItem({ mission, department }: MissionListItemProps) {
  const router = useRouter();
  const href = `/reports/${department}/${mission.command}/${mission.id}`;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => router.push(href)}
      onKeyDown={(e: React.KeyboardEvent) => e.key === "Enter" && router.push(href)}
      style={{
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        padding: "0.75rem 1rem",
        marginBottom: "0.5rem",
        cursor: "pointer",
        transition: "background 0.15s, border-color 0.15s",
      }}
      onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
        e.currentTarget.style.background = "var(--surface-hover)";
        e.currentTarget.style.borderColor = "var(--border-strong)";
      }}
      onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
        e.currentTarget.style.background = "var(--surface-card)";
        e.currentTarget.style.borderColor = "var(--border-subtle)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        {/* Goal / command name */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <span style={{
            fontSize: "0.875rem",
            fontWeight: 500,
            color: "var(--text-primary)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            display: "block",
          }}>
            {mission.command}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {mission.id.slice(0, 8)}
          </span>
        </div>

        {/* Status badge */}
        <Badge
          variant={statusVariant(mission.status)}
          label={statusLabel(mission.status)}
          dot
        />

        {/* Timestamp */}
        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
          {relativeTime(mission.created_at)}
        </span>

        {/* MCU cost placeholder — result_data may carry cost */}
        <span style={{
          fontSize: "0.75rem",
          color: "var(--text-tertiary)",
          whiteSpace: "nowrap",
          fontVariantNumeric: "tabular-nums",
        }}>
          {typeof (mission.result_data as Record<string, unknown>)?.mcu_cost === "number"
            ? `${(mission.result_data as Record<string, unknown>).mcu_cost} MCU`
            : "—"}
        </span>
      </div>
    </div>
  );
}
