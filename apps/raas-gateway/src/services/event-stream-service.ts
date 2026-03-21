/**
 * SSE Event Streaming Service — Server-Sent Events for real-time mission updates
 * Designed for Cloudflare Workers using TransformStream + D1 polling
 */

import type { D1Database } from '@cloudflare/workers-types';

// --- Types ---

export interface SSEMessage {
  event: string; // mission.created | mission.running | mission.completed | mission.failed
  data: unknown;
  id?: string;
  retry?: number;
}

export interface MissionEvent {
  id: string;
  tenant_id: string;
  mission_id: string;
  event_type: string;
  payload: string;
  created_at: string;
}

// In-memory map: tenantId → stream count (CF Worker single-isolate scope)
const activeStreams = new Map<string, number>();

// --- Formatters ---

/**
 * Formats an SSE message per spec: event/data/id/retry fields followed by double newline
 */
export function formatSSEMessage(msg: SSEMessage): string {
  const lines: string[] = [];
  lines.push(`event: ${msg.event}`);
  lines.push(`data: ${JSON.stringify(msg.data)}`);
  if (msg.id) lines.push(`id: ${msg.id}`);
  if (msg.retry !== undefined) lines.push(`retry: ${msg.retry}`);
  lines.push('', ''); // double newline = message boundary
  return lines.join('\n');
}

// --- D1 Queries ---

/**
 * Fetch new mission events for a tenant since a given timestamp
 */
export async function getMissionEvents(
  db: D1Database,
  tenantId: string,
  since: string
): Promise<MissionEvent[]> {
  const result = await db
    .prepare(
      'SELECT * FROM mission_events WHERE tenant_id = ? AND created_at > ? ORDER BY created_at ASC LIMIT 50'
    )
    .bind(tenantId, since)
    .all<MissionEvent>();
  return result.results ?? [];
}

/**
 * Insert a new mission event into D1
 */
export async function publishEvent(
  db: D1Database,
  tenantId: string,
  missionId: string,
  eventType: string,
  payload: unknown
): Promise<void> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db
    .prepare(
      'INSERT INTO mission_events (id, tenant_id, mission_id, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)'
    )
    .bind(id, tenantId, missionId, eventType, JSON.stringify(payload), now)
    .run();
}

// --- Active Stream Tracker ---

/**
 * Returns active stream count — optionally filtered by tenantId
 */
export function getActiveStreams(tenantId?: string): number {
  if (tenantId) return activeStreams.get(tenantId) ?? 0;
  let total = 0;
  for (const count of activeStreams.values()) total += count;
  return total;
}

function incrementStreams(tenantId: string): void {
  activeStreams.set(tenantId, (activeStreams.get(tenantId) ?? 0) + 1);
}

function decrementStreams(tenantId: string): void {
  const count = (activeStreams.get(tenantId) ?? 1) - 1;
  if (count <= 0) activeStreams.delete(tenantId);
  else activeStreams.set(tenantId, count);
}

// --- Stream Factory ---

const POLL_INTERVAL_MS = 2_000;
const MAX_DURATION_MS = 30 * 60 * 1_000; // 30 minutes — CF Worker timeout

/**
 * Creates an SSE ReadableStream that polls D1 every 2s for new mission events.
 * Optionally filters to a single missionId.
 */
export function createSSEStream(
  tenantId: string,
  db: D1Database,
  missionId?: string
): ReadableStream {
  const encoder = new TextEncoder();
  incrementStreams(tenantId);

  let closed = false;

  return new ReadableStream({
    async start(controller) {
      const startedAt = Date.now();
      let since = new Date().toISOString();

      // Initial "connected" event
      controller.enqueue(
        encoder.encode(
          formatSSEMessage({ event: 'connected', data: { tenantId, ts: since }, retry: 3000 })
        )
      );

      const poll = async (): Promise<void> => {
        if (closed) return;
        if (Date.now() - startedAt >= MAX_DURATION_MS) {
          controller.enqueue(
            encoder.encode(formatSSEMessage({ event: 'timeout', data: { reason: 'max_duration_reached' } }))
          );
          controller.close();
          decrementStreams(tenantId);
          return;
        }

        try {
          const events = await getMissionEvents(db, tenantId, since);
          for (const evt of events) {
            if (missionId && evt.mission_id !== missionId) continue;
            const payload = (() => {
              try { return JSON.parse(evt.payload); } catch { return evt.payload; }
            })();
            controller.enqueue(
              encoder.encode(
                formatSSEMessage({ event: evt.event_type, data: { ...payload, mission_id: evt.mission_id }, id: evt.id })
              )
            );
            since = evt.created_at; // advance cursor
          }
        } catch (err) {
          // Non-fatal poll error — log and continue
          console.error('[SSE] poll error:', err);
        }

        await new Promise<void>((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        poll();
      };

      poll();
    },

    cancel() {
      // Client disconnected — stop polling and update counter
      closed = true;
      decrementStreams(tenantId);
    },
  });
}
