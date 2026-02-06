import { Worker } from 'bullmq';
import IORedis from 'ioredis';
import dotenv from 'dotenv';
import prisma from './db.js';
import { executeTask } from './executor.js';
import { safeJSONStringify, withRetry } from './utils.js';

dotenv.config();

const connection = new IORedis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  maxRetriesPerRequest: null,
});

export const worker = new Worker('agency-queue', async (job) => {
  const dbJobId = job.data.id || job.id; // Fallback to job.id if data.id is missing
  console.log(`\n📥 Processing job ${job.id} (DB ID: ${dbJobId})`);

  try {
    // 1. Update status to PROCESSING
    await withRetry(() => prisma.job.update({
      where: { id: dbJobId },
      data: {
        status: 'PROCESSING',
        startedAt: new Date(),
      },
    }));

    const result = await executeTask(job.data);

    // 2. Update status to COMPLETED
    await withRetry(() => prisma.job.update({
      where: { id: dbJobId },
      data: {
        status: 'COMPLETED',
        output: safeJSONStringify(result),
        completedAt: new Date(),
      },
    }));

    console.log(`✅ Job ${job.id} completed`);
    return result;
  } catch (err) {
    console.error(`❌ Job ${job.id} failed:`, err);

    // 3. Update status to FAILED
    try {
      await withRetry(() => prisma.job.update({
        where: { id: dbJobId },
        data: {
          status: 'FAILED',
          error: err.message || 'Unknown error',
          completedAt: new Date(),
        },
      }));
    } catch (dbErr) {
      console.error(`Failed to update job ${dbJobId} status to FAILED:`, dbErr);
    }

    throw err;
  }
}, {
  connection,
  concurrency: 5 // Process 5 jobs in parallel
});

worker.on('completed', (job, returnvalue) => {
  console.log(`Job ${job.id} returned successfully`);
});

worker.on('failed', (job, err) => {
  console.log(`Job ${job.id} has failed with ${err.message}`);
});
