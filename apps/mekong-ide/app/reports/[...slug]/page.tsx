/**
 * Dynamic catch-all report page: /reports/[department]/[command]/[missionId?]
 *
 * Routes:
 *   /reports/marketing/campaign/abc123  → fetch result + render with layout
 *   /reports/marketing/campaign         → no mission: show department index info
 *   /reports/marketing                  → redirect to /reports
 *
 * Uses dynamic import with ssr:false — required for Tauri IPC compatibility.
 */
"use client";

import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useEffect } from "react";
import { getLayout } from "@/lib/report-registry";
import { useMissionResult } from "@/hooks/use-mission-result";

// Dynamic import prevents SSR issues with Tauri IPC bridge
const UniversalReportRenderer = dynamic(
  () =>
    import("@/components/reports/universal-report-renderer").then(
      (m) => m.UniversalReportRenderer
    ),
  { ssr: false }
);

/** Minimal JSON fallback when no layout is registered */
function JsonFallback({ data }: { data: unknown }) {
  return (
    <div style={{ padding: "1.5rem" }}>
      <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "1rem" }}>
        No layout registered for this command. Showing raw output.
      </p>
      <pre
        style={{
          background: "var(--surface-elevated)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "0.5rem",
          padding: "1rem",
          fontSize: "0.75rem",
          color: "var(--text-secondary)",
          overflow: "auto",
          maxHeight: "70vh",
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

/** Loading skeleton */
function LoadingState() {
  return (
    <div style={{ padding: "1.5rem" }}>
      <div
        style={{
          height: "1.5rem",
          width: "240px",
          background: "var(--border-subtle)",
          borderRadius: "0.25rem",
          marginBottom: "1rem",
          animation: "pulse 1.5s infinite",
        }}
      />
      <div
        style={{
          height: "1rem",
          width: "160px",
          background: "var(--border-subtle)",
          borderRadius: "0.25rem",
          animation: "pulse 1.5s infinite",
        }}
      />
    </div>
  );
}

/** No-mission state: prompt user to run a command first */
function NoMissionState({ department, command }: { department: string; command: string }) {
  const router = useRouter();
  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
        No mission ID provided for{" "}
        <strong style={{ color: "var(--text-primary)" }}>
          {department} / {command}
        </strong>
        . Run a command to generate a report.
      </p>
      <button
        onClick={() => router.push("/reports")}
        style={{
          padding: "0.5rem 1.25rem",
          background: "var(--md-sys-color-primary, #6750A4)",
          color: "var(--md-sys-color-on-primary, #fff)",
          border: "none",
          borderRadius: "var(--md-sys-shape-corner-medium, 0.5rem)",
          cursor: "pointer",
          fontSize: "0.875rem",
        }}
      >
        Back to Reports
      </button>
    </div>
  );
}

export default function ReportSlugPage() {
  const params = useParams();
  const router = useRouter();

  // slug = ["department", "command", "missionId?"]
  const rawSlug = params?.slug;
  const slugParts: string[] = Array.isArray(rawSlug)
    ? rawSlug
    : typeof rawSlug === "string"
    ? [rawSlug]
    : [];

  const department = slugParts[0] ?? "";
  const command = slugParts[1] ?? "";
  const missionId = slugParts[2] ?? null;

  // If only department provided (no command), redirect to reports index
  useEffect(() => {
    if (slugParts.length < 2) {
      router.replace("/reports");
    }
  }, [slugParts.length, router]);

  const { data: missionResult, loading, error } = useMissionResult(missionId);

  // Derive layout slug from department + command (e.g. "marketing" + "campaign" → "marketing-campaign")
  const commandSlug = `${department}-${command}`;
  const layout = getLayout(commandSlug);

  if (slugParts.length < 2) return null;

  if (!missionId) {
    return <NoMissionState department={department} command={command} />;
  }

  if (loading) return <LoadingState />;

  if (error) {
    return (
      <div style={{ padding: "1.5rem", color: "var(--text-error, #ef4444)" }}>
        Failed to load mission result: {error}
      </div>
    );
  }

  if (!missionResult) return <LoadingState />;

  if (!layout) {
    return <JsonFallback data={missionResult.result_data} />;
  }

  return <UniversalReportRenderer layout={layout} data={missionResult} />;
}
