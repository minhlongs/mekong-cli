import type { Context } from 'hono'
import type { Bindings } from '../index'

export type HonoContext<B extends object | undefined = { tenant: unknown }> = Context<{ 
  Bindings: Bindings
  Variables: B 
}>

export interface ApiError {
  error: string
  code?: string
  details?: unknown[]
  status?: number
}

export class HttpError extends Error {
  public code: string
  public status: number
  public details?: unknown[]

  constructor(code: string, message: string, details?: unknown[], status?: number) {
    super(message)
    this.name = 'HttpError'
    this.code = code
    this.status = status || 400
    this.details = details
  }

  toResponse(): ApiError {
    return {
      error: this.message,
      code: this.code,
      ...(this.details && { details: this.details }),
      status: this.status
    }
  }
}
