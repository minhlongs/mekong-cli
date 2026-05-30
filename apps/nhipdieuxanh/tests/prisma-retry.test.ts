import { describe, it, expect, vi, beforeEach } from 'vitest'
import { prisma } from '@/lib/prisma'
import { PrismaClient } from '../lib/generated/client'

describe('Prisma Client $transactionWithRetry Extension', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('should execute transaction successfully on the first attempt', async () => {
    const mockTx = vi.fn().mockResolvedValue('success')
    // We mock $transaction on the PrismaClient prototype
    const transactionSpy = vi.spyOn(PrismaClient.prototype, '$transaction').mockImplementation(async function(arg) {
      if (typeof arg === 'function') {
        return arg('mockClient')
      }
      return 'success'
    })

    const result = await prisma.$transactionWithRetry(mockTx)
    expect(result).toBe('success')
    expect(mockTx).toHaveBeenCalledWith('mockClient')
    expect(transactionSpy).toHaveBeenCalledTimes(1)
  })

  it('should retry on transient error and eventually succeed', async () => {
    let attempts = 0
    const mockTx = vi.fn().mockImplementation(async () => {
      attempts++
      if (attempts < 3) {
        const err = new Error('Transaction failed due to a write conflict or a deadlock. Please retry.') as Error & { code?: string }
        err.code = 'P2034'
        throw err
      }
      return 'success_after_retries'
    })

    const transactionSpy = vi.spyOn(PrismaClient.prototype, '$transaction').mockImplementation(async function(arg) {
      if (typeof arg === 'function') {
        return arg('mockClient')
      }
      return 'success'
    })

    const result = await prisma.$transactionWithRetry(mockTx, {
      retries: 3,
      minDelay: 10,
      maxDelay: 50,
    })

    expect(result).toBe('success_after_retries')
    expect(transactionSpy).toHaveBeenCalledTimes(3)
  })

  it('should not retry on non-transient errors', async () => {
    const mockTx = vi.fn().mockImplementation(async () => {
      const err = new Error('Unique constraint failed') as Error & { code?: string }
      err.code = 'P2002'
      throw err
    })

    const transactionSpy = vi.spyOn(PrismaClient.prototype, '$transaction').mockImplementation(async function(arg) {
      if (typeof arg === 'function') {
        return arg('mockClient')
      }
      return 'success'
    })

    await expect(
      prisma.$transactionWithRetry(mockTx, {
        retries: 3,
        minDelay: 10,
      })
    ).rejects.toThrow('Unique constraint failed')

    expect(transactionSpy).toHaveBeenCalledTimes(1)
  })

  it('should throw the last error if retry limit is reached', async () => {
    const mockTx = vi.fn().mockImplementation(async () => {
      const err = new Error('Write conflict deadlock') as Error & { code?: string }
      err.code = 'P2034'
      throw err
    })

    const transactionSpy = vi.spyOn(PrismaClient.prototype, '$transaction').mockImplementation(async function(arg) {
      if (typeof arg === 'function') {
        return arg('mockClient')
      }
      return 'success'
    })

    await expect(
      prisma.$transactionWithRetry(mockTx, {
        retries: 2,
        minDelay: 5,
        maxDelay: 20,
      })
    ).rejects.toThrow('Write conflict deadlock')

    // 1 initial run + 2 retries = 3 calls total
    expect(transactionSpy).toHaveBeenCalledTimes(3)
  })
})
