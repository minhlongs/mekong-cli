import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { VideoPipeline } from '../src/video/pipeline';
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

const createJobParams = (overrides = {}) => ({
  userId: 'user-123',
  topic: 'Test video',
  durationSeconds: 30,
  language: 'en' as const,
  tone: 'professional' as const,
  ...overrides,
});

describe('VideoPipeline', () => {
  let state: ReturnType<typeof createMockState>;
  let pipeline: VideoPipeline;

  beforeEach(() => {
    state = createMockState();
    pipeline = new VideoPipeline(state as any, mockEnv);
  });

  it('should create a job and return it', async () => {
    const job = await pipeline.createJob(createJobParams());

    expect(job).toBeDefined();
    expect(job.id).toMatch(/^job_\d+_[a-z0-9]+$/);
    expect(job.userId).toBe('user-123');
    expect(job.topic).toBe('Test video');
    expect(job.durationSeconds).toBe(30);
    expect(job.status).toBe('pending');
    expect(job.progress).toBe(0);
  });

  it('should retrieve a job by ID', async () => {
    const created = await pipeline.createJob(createJobParams());

    const retrieved = await pipeline.getJob(created.id);
    expect(retrieved).toEqual(created);
  });

  it('should return null for non-existent job', async () => {
    const job = await pipeline.getJob('non-existent');
    expect(job).toBeNull();
  });

  it('should list user jobs', async () => {
    await pipeline.createJob(createJobParams({ userId: 'user-1', topic: 'Video 1', durationSeconds: 10 }));
    // Small delay to ensure different timestamps
    await new Promise(r => setTimeout(r, 10));
    await pipeline.createJob(createJobParams({ userId: 'user-1', topic: 'Video 2', durationSeconds: 20 }));
    await pipeline.createJob(createJobParams({ userId: 'user-2', topic: 'Video 3', durationSeconds: 30 }));

    const user1Jobs = await pipeline.getUserJobs('user-1');
    expect(user1Jobs).toHaveLength(2);
    // Most recent first - Video 2 was created after Video 1
    expect(user1Jobs[0].topic).toBe('Video 2');
    expect(user1Jobs[1].topic).toBe('Video 1');

    const user2Jobs = await pipeline.getUserJobs('user-2');
    expect(user2Jobs).toHaveLength(1);
  });
});

describe('DIDClient', () => {
  it('should create a talk request', () => {
    const client = new DIDClient({ apiKey: 'test-key', baseUrl: 'https://api.d-id.com' });
    // Just verify it instantiates
    expect(client).toBeInstanceOf(DIDClient);
  });
});

describe('ElevenLabsClient', () => {
  it('should create a client instance', () => {
    const client = new ElevenLabsClient({ apiKey: 'test-key', baseUrl: 'https://api.elevenlabs.io/v1' });
    expect(client).toBeInstanceOf(ElevenLabsClient);
  });
});

describe('OpenRouterClient', () => {
  it('should create a client instance', () => {
    const client = new OpenRouterClient({ apiKey: 'test-key', baseUrl: 'https://openrouter.ai/api/v1' });
    expect(client).toBeInstanceOf(OpenRouterClient);
  });
});