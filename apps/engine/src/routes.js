import { z } from 'zod';
import { jobQueue } from './queue.js';
import prisma from './db.js';

const CompletionSchema = z.object({
  model: z.string().default('gemini-1.5-pro'),
  messages: z.array(
    z.object({
      role: z.string(),
      content: z.string(),
    })
  ).min(1),
  temperature: z.number().optional().default(0.7),
  userId: z.string().optional(), // Optional for now, passed from Gateway
});

export default async function routes(fastify, options) {
  fastify.post('/v1/chat/completions', async (request, reply) => {
    // 1. Auth Check (Basic Service Token)
    const authHeader = request.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return reply.code(401).send({ error: { message: 'Missing Authorization header' } });
    }

    // In production, compare with process.env.SERVICE_TOKEN
    // For now, allow any token in dev

    // 2. Validation
    const parseResult = CompletionSchema.safeParse(request.body);
    if (!parseResult.success) {
      return reply.code(400).send({ error: { message: 'Invalid request body', details: parseResult.error } });
    }

    const { model, messages, userId } = parseResult.data;

    try {
      // 3. Persist Job to Database (Postgres)
      const jobRecord = await prisma.job.create({
        data: {
          type: 'chat.completion',
          status: 'QUEUED',
          input: JSON.stringify({ model, messages }),
          userId: userId || null,
        }
      });

      const jobId = jobRecord.id;

      // 4. Add to Queue (Redis)
      await jobQueue.add('chat.completion', {
        id: jobId,
        model,
        messages,
        timestamp: Date.now()
      }, {
        jobId, // Use Postgres ID as BullMQ ID for consistency
        removeOnComplete: 1000,
        removeOnFail: 5000
      });

      // 5. Respond immediately
      return {
        id: jobId,
        object: 'chat.completion.queued',
        created: Math.floor(Date.now() / 1000),
        model: model,
        status: 'queued',
        message: 'Job accepted and queued for processing'
      };
    } catch (err) {
      request.log.error(err);
      return reply.code(500).send({ error: { message: 'Internal Engine Error', details: err.message } });
    }
  });

  fastify.get('/v1/jobs/:id', async (request, reply) => {
    const { id } = request.params;

    // 1. Auth Check (Basic Service Token)
    const authHeader = request.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return reply.code(401).send({ error: { message: 'Missing Authorization header' } });
    }

    try {
      const job = await prisma.job.findUnique({
        where: { id }
      });

      if (!job) {
        return reply.code(404).send({ error: { message: 'Job not found' } });
      }

      return {
        id: job.id,
        object: 'chat.completion.job',
        created: Math.floor(job.createdAt.getTime() / 1000),
        status: job.status.toLowerCase(), // queued, processing, completed, failed
        result: job.output ? JSON.parse(job.output) : null,
        error: job.error || null
      };
    } catch (err) {
      request.log.error(err);
      return reply.code(500).send({ error: { message: 'Internal Engine Error', details: err.message } });
    }
  });

  fastify.get('/health', async () => {
    return { status: 'ok', uptime: process.uptime() };
  });
}
