"use client";

/**
 * Department index page — lists all missions for a given department.
 * Route: /reports/[department]  (e.g. /reports/marketing)
 * Fetches GET /v1/tasks?department={dept}&limit=20 via useMissionList hook.
 */

import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import { useMissionList } from "@/hooks/use-mission-list";
import { getDepartment } from "@/lib/department-config";

/* Lazy-load the mission row to keep initial chunk lean */
const MissionListItem = dynamic(
  () => import("@/components/reports/mission-list-item").then((m) => m.MissionListItem),
  { ssr: false }
);

export default function DepartmentPage() {
  const params = useParams<{ department: string }>();
  const router = useRouter();
  const department = params?.department ?? "";
  const deptInfo = getDepartment(department);

  const { missions, loading, error } = useMissionList(department);

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <button
          onClick={() => router.push("/reports")}
          style={{
            background: "none",
            border: "none",
            color: "var(--text-secondary)",
            cursor: "pointer",
            fontSize: "0.875rem",
            padding: 0,
          }}
        >
          Reports
        </button>
        <span style={{ color: "var(--text-tertiary)" }}>/</span>
        <span style={{ fontSize: "0.875rem", color: "var(--text-primary)", fontWeight: 500 }}>
          {deptInfo?.name ?? department.charAt(0).toUpperCase() + department.slice(1)}
        </span>
      </div>

      {/* Heading */}
      <h1 style={{
        fontSize: "1.5rem",
        fontWeight: 700,
        color: "var(--text-primary)",
        marginBottom: "0.25rem",
      }}>
        {deptInfo?.name ?? department} Reports
      </h1>
      {deptInfo && (
        <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
          {deptInfo.tagline}
        </p>
      )}

      {/* Loading */}
      {loading && (
        <p style={{ color: "var(--text-tertiary)", fontSize: "0.875rem" }}>Loading missions…</p>
      )}

      {/* Error */}
      {error && (
        <p style={{ color: "var(--status-danger)", fontSize: "0.875rem" }}>
          Error loading missions: {error}
        </p>
      )}

      {/* Empty state */}
      {!loading && !error && missions && missions.length === 0 && (
        <div style={{
          textAlign: "center",
          padding: "3rem",
          color: "var(--text-tertiary)",
          border: "1px dashed var(--border-subtle)",
          borderRadius: "0.5rem",
        }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.75rem" }}>—</div>
          <p style={{ fontSize: "0.875rem" }}>No missions yet.</p>
          <p style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
            Run a command to get started.
          </p>
        </div>
      )}

      {/* Mission list */}
      {!loading && missions && missions.length > 0 && (
        <div>
          {missions.map((m) => (
            <MissionListItem key={m.id} mission={m} department={department} />
          ))}
        </div>
      )}
    </div>
  );
}
