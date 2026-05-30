import { PrismaClient } from './generated/client'

const globalForPrisma = global as unknown as { prisma: unknown }

// Helper to determine if an error is transient
function isTransientError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false

  const errObj = error as Record<string, unknown>
  if (errObj.code && typeof errObj.code === 'string') {
    const transientCodes = ['P2034', 'P2028', 'P1001', 'P1008', 'P1017']
    if (transientCodes.includes(errObj.code)) {
      return true
    }
  }

  const message = (errObj.message as string | undefined)?.toLowerCase() || ''
  if (
    message.includes('deadlock') ||
    message.includes('write conflict') ||
    message.includes('transaction failed') ||
    message.includes('connection limit') ||
    message.includes('pool timeout') ||
    message.includes('timeout')
  ) {
    return true
  }

  return false
}

const basePrisma = new PrismaClient()

interface RetryOptions {
  maxWait?: number
  timeout?: number
  isolationLevel?: unknown
  retries?: number
  minDelay?: number
  maxDelay?: number
}

interface PrismaExtendedClient {
  $transaction: <T>(arg: unknown, options?: unknown) => Promise<T>
}

export const prisma = basePrisma.$extends({
  client: {
    async $transactionWithRetry<T>(
      this: unknown,
      arg: unknown,
      options?: RetryOptions
    ): Promise<T> {
      const retries = options?.retries ?? 5
      const minDelay = options?.minDelay ?? 100 // ms
      const maxDelay = options?.maxDelay ?? 3000 // ms

      let lastError: unknown = null
      const client = this as PrismaExtendedClient

      for (let attempt = 0; attempt <= retries; attempt++) {
        try {
          return await client.$transaction<T>(arg, options)
        } catch (error: unknown) {
          lastError = error

          if (attempt < retries && isTransientError(error)) {
            const delay = Math.min(maxDelay, minDelay * Math.pow(2, attempt))
            const jitter = Math.random() * delay
            const sleepTime = Math.round(jitter)

            const errObj = error as Record<string, unknown>
            const errMsg = (errObj.message as string | undefined) || String(error)
            const errCode = (errObj.code as string | undefined) || 'unknown'

            console.warn(
              `[Prisma Transaction Retry] Attempt ${attempt + 1} failed (code: ${errCode}). Retrying in ${sleepTime}ms. Error: ${errMsg}`
            )

            await new Promise((resolve) => setTimeout(resolve, sleepTime))
          } else {
            throw error
          }
        }
      }
      throw lastError
    },
  },
})

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma


