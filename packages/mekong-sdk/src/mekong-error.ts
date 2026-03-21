/**
 * MekongError — structured error thrown by all MekongClient methods
 */
export class MekongError extends Error {
  /** HTTP status code (0 for network/timeout errors) */
  readonly status: number
  /** Machine-readable error code from API or generic code */
  readonly code: string
  /** Raw response body from API (if available) */
  readonly data?: unknown

  constructor(message: string, status: number, code: string, data?: unknown) {
    super(message)
    this.name = 'MekongError'
    this.status = status
    this.code = code
    this.data = data
  }

  static fromResponse(status: number, body: Record<string, unknown>): MekongError {
    const message = (body.error as string) || (body.message as string) || `HTTP ${status}`
    const code = (body.code as string) || `HTTP_${status}`
    return new MekongError(message, status, code, body)
  }

  static network(cause: unknown): MekongError {
    const message = cause instanceof Error ? cause.message : 'Network error'
    return new MekongError(message, 0, 'NETWORK_ERROR', cause)
  }

  static timeout(): MekongError {
    return new MekongError('Request timed out', 0, 'TIMEOUT')
  }
}
