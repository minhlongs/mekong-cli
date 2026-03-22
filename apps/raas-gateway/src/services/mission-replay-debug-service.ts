/**
 * Mission Replay & Debug Service — step-by-step execution trace, replay, debug sessions
 */

export interface ExecutionStep {
  id: string;
  tenant_id: string;
  mission_id: string;
  step_number: number;
  step_type: string;
  input_data: string | null;
  output_data: string | null;
  duration_ms: number | null;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface DebugSession {
  id: string;
  tenant_id: string;
  mission_id: string;
  debug_mode: string;
  breakpoints: string;
  current_step: number;
  session_status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReplayLog {
  id: string;
  tenant_id: string;
  mission_id: string;
  original_mission_id: string;
  replay_status: string;
  divergence_point: number | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Execution Steps
// ---------------------------------------------------------------------------

export async function getExecutionSteps(
  db: D1Database,
  tenantId: string,
  missionId: string
): Promise<ExecutionStep[]> {
  const result = await db
    .prepare(
      'SELECT * FROM mission_execution_steps WHERE tenant_id = ? AND mission_id = ? ORDER BY step_number ASC'
    )
    .bind(tenantId, missionId)
    .all<ExecutionStep>();
  return result.results;
}

export async function recordStep(
  db: D1Database,
  tenantId: string,
  missionId: string,
  step: {
    step_number: number;
    step_type: string;
    input_data?: string;
    output_data?: string;
    duration_ms?: number;
    status?: string;
    error_message?: string;
  }
): Promise<ExecutionStep> {
  const inserted = await db
    .prepare(
      `INSERT INTO mission_execution_steps
        (tenant_id, mission_id, step_number, step_type, input_data, output_data, duration_ms, status, error_message)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
       RETURNING *`
    )
    .bind(
      tenantId,
      missionId,
      step.step_number,
      step.step_type,
      step.input_data ?? null,
      step.output_data ?? null,
      step.duration_ms ?? null,
      step.status ?? 'completed',
      step.error_message ?? null
    )
    .first<ExecutionStep>();
  if (!inserted) throw new Error('Failed to record step');
  return inserted;
}

// ---------------------------------------------------------------------------
// Debug Sessions
// ---------------------------------------------------------------------------

export async function createDebugSession(
  db: D1Database,
  tenantId: string,
  body: { mission_id: string; debug_mode?: string; breakpoints?: number[]; notes?: string }
): Promise<DebugSession> {
  const session = await db
    .prepare(
      `INSERT INTO mission_debug_sessions (tenant_id, mission_id, debug_mode, breakpoints, notes)
       VALUES (?, ?, ?, ?, ?)
       RETURNING *`
    )
    .bind(
      tenantId,
      body.mission_id,
      body.debug_mode ?? 'trace',
      JSON.stringify(body.breakpoints ?? []),
      body.notes ?? null
    )
    .first<DebugSession>();
  if (!session) throw new Error('Failed to create debug session');
  return session;
}

export async function getDebugSession(
  db: D1Database,
  tenantId: string,
  sessionId: string
): Promise<DebugSession | null> {
  return db
    .prepare('SELECT * FROM mission_debug_sessions WHERE id = ? AND tenant_id = ?')
    .bind(sessionId, tenantId)
    .first<DebugSession>();
}

export async function updateDebugSession(
  db: D1Database,
  tenantId: string,
  sessionId: string,
  updates: { current_step?: number; session_status?: string; notes?: string; breakpoints?: number[] }
): Promise<DebugSession | null> {
  const fields: string[] = ['updated_at = datetime(\'now\')'];
  const values: unknown[] = [];
  if (updates.current_step !== undefined) { fields.push('current_step = ?'); values.push(updates.current_step); }
  if (updates.session_status !== undefined) { fields.push('session_status = ?'); values.push(updates.session_status); }
  if (updates.notes !== undefined) { fields.push('notes = ?'); values.push(updates.notes); }
  if (updates.breakpoints !== undefined) { fields.push('breakpoints = ?'); values.push(JSON.stringify(updates.breakpoints)); }
  values.push(sessionId, tenantId);
  return db
    .prepare(`UPDATE mission_debug_sessions SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ? RETURNING *`)
    .bind(...values)
    .first<DebugSession>();
}

// ---------------------------------------------------------------------------
// Replay
// ---------------------------------------------------------------------------

export async function startReplay(
  db: D1Database,
  tenantId: string,
  originalMissionId: string
): Promise<ReplayLog> {
  const log = await db
    .prepare(
      `INSERT INTO mission_replay_logs (tenant_id, mission_id, original_mission_id, replay_status)
       VALUES (?, ?, ?, 'running')
       RETURNING *`
    )
    .bind(tenantId, originalMissionId, originalMissionId)
    .first<ReplayLog>();
  if (!log) throw new Error('Failed to start replay');
  return log;
}

export async function getReplayStatus(
  db: D1Database,
  tenantId: string,
  replayId: string
): Promise<ReplayLog | null> {
  return db
    .prepare('SELECT * FROM mission_replay_logs WHERE id = ? AND tenant_id = ?')
    .bind(replayId, tenantId)
    .first<ReplayLog>();
}

// ---------------------------------------------------------------------------
// Trace & Admin
// ---------------------------------------------------------------------------

export async function getMissionTrace(
  db: D1Database,
  tenantId: string,
  missionId: string
): Promise<{ steps: ExecutionStep[]; sessions: DebugSession[]; replays: ReplayLog[] }> {
  const [stepsRes, sessionsRes, replaysRes] = await Promise.all([
    db.prepare('SELECT * FROM mission_execution_steps WHERE tenant_id = ? AND mission_id = ? ORDER BY step_number ASC').bind(tenantId, missionId).all<ExecutionStep>(),
    db.prepare('SELECT * FROM mission_debug_sessions WHERE tenant_id = ? AND mission_id = ? ORDER BY created_at DESC').bind(tenantId, missionId).all<DebugSession>(),
    db.prepare('SELECT * FROM mission_replay_logs WHERE tenant_id = ? AND original_mission_id = ? ORDER BY created_at DESC').bind(tenantId, missionId).all<ReplayLog>(),
  ]);
  return { steps: stepsRes.results, sessions: sessionsRes.results, replays: replaysRes.results };
}

export async function getAdminOverview(db: D1Database): Promise<{
  total_steps: number;
  total_sessions: number;
  total_replays: number;
  active_sessions: number;
  diverged_replays: number;
}> {
  const [steps, sessions, replays, activeSessions, diverged] = await Promise.all([
    db.prepare('SELECT COUNT(*) as n FROM mission_execution_steps').first<{ n: number }>(),
    db.prepare('SELECT COUNT(*) as n FROM mission_debug_sessions').first<{ n: number }>(),
    db.prepare('SELECT COUNT(*) as n FROM mission_replay_logs').first<{ n: number }>(),
    db.prepare("SELECT COUNT(*) as n FROM mission_debug_sessions WHERE session_status = 'active'").first<{ n: number }>(),
    db.prepare("SELECT COUNT(*) as n FROM mission_replay_logs WHERE replay_status = 'diverged'").first<{ n: number }>(),
  ]);
  return {
    total_steps: steps?.n ?? 0,
    total_sessions: sessions?.n ?? 0,
    total_replays: replays?.n ?? 0,
    active_sessions: activeSessions?.n ?? 0,
    diverged_replays: diverged?.n ?? 0,
  };
}
