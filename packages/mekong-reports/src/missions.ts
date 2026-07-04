/**
 * Mission data layer.
 * Stub implementation — returns mock missions matching Gateway contract:
 *   GET /v1/missions → { missions: Mission[] }
 * When backend ships (C1 phase), replace fetch logic here only.
 */

import type { Mission, ReportPage } from "./types.js";

// ─── Mock data ───────────────────────────────────────────────────────────────

const MOCK_MISSIONS: Mission[] = [
  {
    id: "msn_001",
    title: "Bootstrap ide-ui Next.js 15 App Router",
    status: "completed",
    createdAt: "2026-04-17T08:00:00.000Z",
    completedAt: "2026-04-17T09:15:00.000Z",
    mcuUsed: 5,
  },
  {
    id: "msn_002",
    title: "mekong-reports contract package (B2)",
    status: "running",
    createdAt: "2026-04-17T10:05:00.000Z",
  },
  {
    id: "msn_003",
    title: "Tauri shell scaffold (B3)",
    status: "pending",
    createdAt: "2026-04-17T10:05:00.000Z",
  },
];

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Get a single mission by id.
 * Returns undefined when not found (caller decides how to handle).
 */
export async function getMission(id: string): Promise<ReportPage<Mission | null>> {
  const mission = MOCK_MISSIONS.find((m) => m.id === id) ?? null;
  return {
    data: mission,
    fetchedAt: Date.now(),
    source: "mock",
  };
}

/**
 * List all missions, optionally filtered by status.
 * Matches Gateway contract: GET /v1/missions?status=<value>
 */
export async function listMissions(
  filter?: { status?: Mission["status"] }
): Promise<ReportPage<Mission[]>> {
  const data = filter?.status
    ? MOCK_MISSIONS.filter((m) => m.status === filter.status)
    : MOCK_MISSIONS;

  return {
    data,
    fetchedAt: Date.now(),
    source: "mock",
  };
}
