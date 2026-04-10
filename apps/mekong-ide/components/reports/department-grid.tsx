/**
 * Department grid for the /reports/ landing page.
 * Shows all departments as clickable cards with icon, name, tagline, and mission count.
 * Department metadata sourced from lib/department-config.ts (derived from tenants/*.json).
 */
"use client";

import type React from "react";
import { useRouter } from "next/navigation";
import { getDepartments } from "@/lib/department-config";

interface DepartmentGridProps {
  /** Optional per-department mission counts, keyed by slug */
  missionCounts?: Record<string, number>;
}

export function DepartmentGrid({ missionCounts = {} }: DepartmentGridProps) {
  const router = useRouter();
  const departments = getDepartments();

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
        gap: "0.75rem",
      }}
    >
      {departments.map((dept) => {
        const count = missionCounts[dept.slug] ?? 0;
        return (
          <div
            key={dept.slug}
            role="button"
            tabIndex={0}
            onClick={() => router.push(`/reports/${dept.slug}/`)}
            onKeyDown={(e: React.KeyboardEvent) => e.key === "Enter" && router.push(`/reports/${dept.slug}/`)}
            style={{
              background: "var(--surface-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0.5rem",
              padding: "1rem",
              cursor: "pointer",
              transition: "background 0.15s, border-color 0.15s",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
            onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
              const el = e.currentTarget;
              el.style.background = "var(--surface-hover)";
              el.style.borderColor = dept.accentColor;
            }}
            onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
              const el = e.currentTarget;
              el.style.background = "var(--surface-card)";
              el.style.borderColor = "var(--border-subtle)";
            }}
          >
            {/* Icon accent dot */}
            <div
              style={{
                width: "2rem",
                height: "2rem",
                borderRadius: "0.375rem",
                background: `${dept.accentColor}22`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1rem",
              }}
              aria-hidden
            >
              <span style={{ color: dept.accentColor, fontSize: "0.875rem", fontWeight: 700 }}>
                {dept.name.charAt(0)}
              </span>
            </div>

            {/* Name */}
            <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
              {dept.name}
            </div>

            {/* Tagline */}
            <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", lineHeight: 1.4 }}>
              {dept.tagline}
            </div>

            {/* Mission count */}
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "auto" }}>
              {count > 0 ? `${count} mission${count !== 1 ? "s" : ""}` : "No missions yet"}
            </div>
          </div>
        );
      })}
    </div>
  );
}
