/** Unique identifier */
export type Id = string;

/** ISO timestamp */
export type Timestamp = string;

/** Priority levels aligned with TPS urgency */
export type Priority = 'low' | 'normal' | 'high' | 'critical';

/** Execution status */
export type Status = 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'skipped';

/** Result wrapper - use instead of throw for expected errors */
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

/** Create success result */
export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

/** Create error result */
export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

/** Base error class for mekong-cli */
export class MekongError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly recoverable: boolean = true,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'MekongError';
  }
}
