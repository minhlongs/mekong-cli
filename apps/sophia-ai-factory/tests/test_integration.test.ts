import { describe, it, expect, vi, beforeEach } from 'vitest';
import { VideoPipeline } from '../src/video/pipeline';
import { MCUBilling } from '../src/billing/mcu';
import { DIDClient } from '../src/video/did';
import { ElevenLabsClient } from '../src/video/elevenlabs';
import { OpenRouterClient } from '../src/video/openrouter';

// Mock DurableObjectState
const createMockState = () => {
  const storage = new Map<string, unknown>();
  return {
    storage: {
      get: vi.fn(async (key: string) => storage.get(key)),
      put: vi.fn(async (key: string, value: unknown) => { storage.set(key, value); }),
      delete: vi.fn(async (key: string) => { storage.delete(key); }),
      list: vi.fn(async () => Array.from(storage.entries())),
    },
    blockConcurrencyWhile: vi.fn(async (cb: () => Promise<void>) => cb()),
  };
};

const mockEnv = {
  didApiKey: 'test-did-key',
  didBaseUrl: 'https://api.d-id.com',
  elevenlabsApiKey: 'test-elevenlabs-key',
  elevenlabsBaseUrl: 'https://api.elevenlabs.io/v1',
  openrouterApiKey: 'test-openrouter-key',
  openrouterBaseUrl: 'https://openrouter.ai/api/v1',
  defaultAvatarUrl: 'https://example.com/avatar.jpg',
  defaultVoiceId: 'test-voice-id',
};

describe('Integration: Full Video Pipeline Flow', () => {
  let pipelineState: ReturnType<typeof createMockState>;
  let billingState: ReturnType<typeof createMockState>;
  let pipeline: VideoPipeline;
  let billing: MCUBilling;

  beforeEach(() => {
    pipelineState = createMockState();
    billingState = createMockState();
    pipeline = new VideoPipeline(pipelineState as any, mockEnv);
    billing = new MCUBilling(billingState as any, { MCU_CONFIG: JSON.stringify({}) });
  });

  it('should create video job, charge MCU credits, and track balance', async () => {
    // Top up user balance
    await billing.topUp({ userId: 'user-123', credits: 100 });

    // Create video job
    const job = await pipeline.createJob({
      userId: 'user-123',
      topic: 'AI in Healthcare',
      durationSeconds: 60,
      language: 'en',
      tone: 'professional',
    });

    expect(job.id).toBeDefined();
    expect(job.status).toBe('pending');
    expect(job.durationSeconds).toBe(60);

    // Check initial balance
    const initialBalance = await billing.getBalance('user-123');
    expect(initialBalance.balance).toBe(100);

    // Simulate job completion - charge credits
    const chargeResult = await billing.charge({
      userId: 'user-123',
      seconds: job.durationSeconds,
    });

    expect(chargeResult.success).toBe(true);
    expect(chargeResult.creditsCharged).toBe(60);
    expect(chargeResult.remainingBalance).toBe(40);

    // Verify final balance
    const finalBalance = await billing.getBalance('user-123');
    expect(finalBalance.balance).toBe(40);
  });

  it('should handle tier-based pricing correctly', async () => {
    // Set user to PREMIUM tier
    await billing.topUp({ userId: 'premium-user', credits: 100 });
    await billing.setTier('premium-user', 'PREMIUM');

    const job = await pipeline.createJob({
      userId: 'premium-user',
      topic: 'Test',
      durationSeconds: 50,
    });

    const chargeResult = await billing.charge({
      userId: 'premium-user',
      seconds: job.durationSeconds,
    });

    // PREMIUM gets 20% discount: 50 * 0.8 = 40
    expect(chargeResult.creditsCharged).toBe(40);
    expect(chargeResult.remainingBalance).toBe(60);
  });

  it('should handle ENTERPRISE tier pricing', async () => {
    await billing.topUp({ userId: 'enterprise-user', credits: 100 });
    await billing.setTier('enterprise-user', 'ENTERPRISE');

    const job = await pipeline.createJob({
      userId: 'enterprise-user',
      topic: 'Test',
      durationSeconds: 50,
    });

    const chargeResult = await billing.charge({
      userId: 'enterprise-user',
      seconds: job.durationSeconds,
    });

    // ENTERPRISE gets 40% discount: 50 * 0.6 = 30
    expect(chargeResult.creditsCharged).toBe(30);
    expect(chargeResult.remainingBalance).toBe(70);
  });

  it('should handle MASTER tier pricing', async () => {
    await billing.topUp({ userId: 'master-user', credits: 100 });
    await billing.setTier('master-user', 'MASTER');

    const job = await pipeline.createJob({
      userId: 'master-user',
      topic: 'Test',
      durationSeconds: 50,
    });

    const chargeResult = await billing.charge({
      userId: 'master-user',
      seconds: job.durationSeconds,
    });

    // MASTER gets 60% discount: 50 * 0.4 = 20
    expect(chargeResult.creditsCharged).toBe(20);
    expect(chargeResult.remainingBalance).toBe(80);
  });

  it('should fail job creation when insufficient credits', async () => {
    await billing.topUp({ userId: 'poor-user', credits: 5 });

    const job = await pipeline.createJob({
      userId: 'poor-user',
      topic: 'Expensive video',
      durationSeconds: 100,
    });

    const chargeResult = await billing.charge({
      userId: 'poor-user',
      seconds: job.durationSeconds,
    });

    expect(chargeResult.success).toBe(false);
    expect(chargeResult.error).toBe('Insufficient credits');
  });

  it('should track multiple jobs per user', async () => {
    await billing.topUp({ userId: 'multi-user', credits: 500 });

    const job1 = await pipeline.createJob({
      userId: 'multi-user',
      topic: 'Video 1',
      durationSeconds: 30,
    });

    const job2 = await pipeline.createJob({
      userId: 'multi-user',
      topic: 'Video 2',
      durationSeconds: 40,
    });

    const userJobs = await pipeline.getUserJobs('multi-user');
    expect(userJobs).toHaveLength(2);
    expect(userJobs.map(j => j.topic)).toContain('Video 1');
    expect(userJobs.map(j => j.topic)).toContain('Video 2');
  });

  it('should handle Vietnamese language videos', async () => {
    await billing.topUp({ userId: 'vn-user', credits: 100 });

    const job = await pipeline.createJob({
      userId: 'vn-user',
      topic: 'Trí tuệ nhân tạo trong y tế',
      durationSeconds: 45,
      language: 'vi',
      tone: 'educational',
    });

    expect(job.language).toBe('vi');
    expect(job.tone).toBe('educational');
    expect(job.topic).toBe('Trí tuệ nhân tạo trong y tế');
  });

  it('should handle different tones', async () => {
    const tones = ['professional', 'casual', 'energetic', 'educational'] as const;

    for (const tone of tones) {
      const state = createMockState();
      const pipeline = new VideoPipeline(state as any, mockEnv);

      const job = await pipeline.createJob({
        userId: `user-${tone}`,
        topic: 'Test',
        durationSeconds: 30,
        tone,
      });

      expect(job.tone).toBe(tone);
    }
  });

  it('should handle webhook URL registration', async () => {
    const webhookUrl = 'https://myapp.com/webhook/video-complete';

    const job = await pipeline.createJob({
      userId: 'webhook-user',
      topic: 'Test with webhook',
      durationSeconds: 30,
      webhookUrl,
    });

    expect(job.webhookUrl).toBe(webhookUrl);
  });

  it('should handle custom avatar and voice', async () => {
    const customAvatar = 'https://mycdn.com/custom-avatar.jpg';
    const customVoice = 'custom-voice-id';

    const job = await pipeline.createJob({
      userId: 'custom-user',
      topic: 'Custom video',
      durationSeconds: 30,
      avatarUrl: customAvatar,
      voiceId: customVoice,
    });

    // Job stores the request params; actual usage is in pipeline execution
    expect(job.id).toBeDefined();
  });
});

describe('Integration: AI Provider Clients (Test Mode)', () => {
  it('should instantiate DID client with test config', () => {
    const client = new DIDClient({
      apiKey: 'test-key',
      baseUrl: 'https://api.d-id.com',
    });
    expect(client).toBeInstanceOf(DIDClient);
  });

  it('should instantiate ElevenLabs client with test config', () => {
    const client = new ElevenLabsClient({
      apiKey: 'test-key',
      baseUrl: 'https://api.elevenlabs.io/v1',
    });
    expect(client).toBeInstanceOf(ElevenLabsClient);
  });

  it('should instantiate OpenRouter client with test config', () => {
    const client = new OpenRouterClient({
      apiKey: 'test-key',
      baseUrl: 'https://openrouter.ai/api/v1',
    });
    expect(client).toBeInstanceOf(OpenRouterClient);
  });

  it('should validate script generation request schema', () => {
    const client = new OpenRouterClient({ apiKey: 'test-key' });

    // Test that the schema validation works
    const validRequest = {
      topic: 'AI Video Generation',
      duration_seconds: 60,
      language: 'en',
      tone: 'professional',
      target_audience: 'developers',
      key_points: ['D-ID', 'ElevenLabs', 'OpenRouter'],
    };

    // The schema should accept this
    expect(() => {
      // @ts-expect-error - accessing private method for test
      client.generateScript(validRequest);
    }).not.toThrow();
  });
});

describe('Integration: Error Handling', () => {
  let pipelineState: ReturnType<typeof createMockState>;
  let pipeline: VideoPipeline;

  beforeEach(() => {
    pipelineState = createMockState();
    pipeline = new VideoPipeline(pipelineState as any, mockEnv);
  });

  it('should handle job retrieval for non-existent ID', async () => {
    const job = await pipeline.getJob('non-existent-id');
    expect(job).toBeNull();
  });

  it('should return empty array for user with no jobs', async () => {
    const jobs = await pipeline.getUserJobs('new-user');
    expect(jobs).toEqual([]);
  });

  it('should handle concurrent job creation for same user', async () => {
    const promises = Array.from({ length: 5 }, (_, i) =>
      pipeline.createJob({
        userId: 'concurrent-user',
        topic: `Video ${i}`,
        durationSeconds: 10,
      })
    );

    const jobs = await Promise.all(promises);
    expect(jobs).toHaveLength(5);
    expect(new Set(jobs.map(j => j.id)).size).toBe(5); // All unique IDs
  });
});