/**
 * Secure Job Queue & Audit Logging for Compliance Tasks
 */

import Redis from 'ioredis'
import crypto from 'crypto'
import { securityLogger } from './logger'
import type { JobPayload, SecureJob } from './compliance-types'

export class SecureJobQueue {
  private redis: Redis
  private jobSecret: string

  constructor() {
    this.jobSecret = process.env.JOB_SECRET || crypto.randomBytes(32).toString('hex')
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'redis.internal',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD,
      maxRetriesPerRequest: 3,
      lazyConnect: true,
    })
  }

  generateJobToken(requestId: string, jobType: string): string {
    const payload = `${requestId}:${jobType}:${Date.now()}`
    return crypto.createHmac('sha256', this.jobSecret).update(payload).digest('hex')
  }

  verifyJobToken(token: string, requestId: string, jobType: string): boolean {
    const expectedToken = this.generateJobToken(requestId, jobType)
    return crypto.timingSafeEqual(Buffer.from(token), Buffer.from(expectedToken))
  }

  async enqueue(jobType: string, payload: JobPayload): Promise<string> {
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const job: SecureJob = {
      id: jobId,
      type: jobType,
      payload,
      jobToken: payload.jobToken,
      userId: payload.userId,
      queuedAt: payload.queuedAt,
      expiresAt: payload.expiresAt,
      attempts: 0,
      maxAttempts: 3,
      status: 'pending',
    }

    await this.redis.setex(`job:${jobId}`, 24 * 60 * 60, JSON.stringify(job))
    await this.redis.lpush(`queue:${jobType}`, jobId)
    return jobId
  }

  async dequeue(jobType: string): Promise<SecureJob | null> {
    const jobId = await this.redis.brpoplpush(`queue:${jobType}`, `processing:${jobType}`, 10)
    if (!jobId) return null

    const jobData = await this.redis.get(`job:${jobId}`)
    if (!jobData) return null

    const job: SecureJob = JSON.parse(jobData)
    if (new Date(job.expiresAt) < new Date()) {
      await this.redis.del(`job:${jobId}`)
      return null
    }

    if (!this.verifyJobToken(job.jobToken, job.payload.requestId, job.type)) {
      await securityLogger.security('malicious_request', 'Invalid job token detected', { jobId })
      await this.redis.del(`job:${jobId}`)
      return null
    }

    job.status = 'processing'
    job.attempts++
    await this.redis.setex(`job:${jobId}`, 24 * 60 * 60, JSON.stringify(job))
    return job
  }

  async completeJob(jobId: string, _result?: Record<string, unknown>): Promise<void> {
    const jobData = await this.redis.get(`job:${jobId}`)
    if (!jobData) return

    const job: SecureJob = JSON.parse(jobData)
    job.status = 'completed'
    await this.redis.setex(`job:${jobId}`, 7 * 24 * 60 * 60, JSON.stringify(job))
    await this.redis.lrem(`processing:${job.type}`, 1, jobId)

    await securityLogger.security('admin_action', 'Background job completed', {
      jobId,
      jobType: job.type,
      userId: job.userId,
    })
  }

  async failJob(jobId: string, error: Error): Promise<void> {
    const jobData = await this.redis.get(`job:${jobId}`)
    if (!jobData) return

    const job: SecureJob = JSON.parse(jobData)
    if (job.attempts >= job.maxAttempts) {
      job.status = 'failed'
      await securityLogger.error('Background job failed permanently', error, {
        jobId,
        jobType: job.type,
        userId: job.userId,
        attempts: job.attempts,
      })
    } else {
      await this.redis.lpush(`queue:${job.type}`, jobId)
    }

    await this.redis.lrem(`processing:${job.type}`, 1, jobId)
    await this.redis.setex(`job:${jobId}`, 24 * 60 * 60, JSON.stringify(job))
  }

  async getJobStatus(jobId: string): Promise<SecureJob | null> {
    const jobData = await this.redis.get(`job:${jobId}`)
    return jobData ? JSON.parse(jobData) : null
  }

  async cleanupExpiredJobs(): Promise<number> {
    const patterns = ['job:*']
    let cleanedCount = 0

    for (const pattern of patterns) {
      const keys = await this.redis.keys(pattern)
      for (const key of keys) {
        const jobData = await this.redis.get(key)
        if (jobData) {
          const job: SecureJob = JSON.parse(jobData)
          if (new Date(job.expiresAt) < new Date()) {
            await this.redis.del(key)
            cleanedCount++
          }
        }
      }
    }
    return cleanedCount
  }
}
