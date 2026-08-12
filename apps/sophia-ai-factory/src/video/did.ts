import { z } from 'zod';

export const DIDConfigSchema = z.object({
  apiKey: z.string().min(1),
  baseUrl: z.string().url().default('https://api.d-id.com'),
});

export type DIDConfig = z.infer<typeof DIDConfigSchema>;

export const CreateTalkRequestSchema = z.object({
  script: z.object({
    type: z.literal('text'),
    input: z.string().min(1).max(5000),
    provider: z.object({
      type: z.literal('microsoft'),
      voice_id: z.string().optional(),
    }).optional(),
  }),
  source_url: z.string().url(),
  config: z.object({
    fluent: z.boolean().default(false),
    pad_audio: z.number().min(0).default(0),
    driver_url: z.string().url().optional(),
  }).optional(),
});

export type CreateTalkRequest = z.infer<typeof CreateTalkRequestSchema>;

export const DIDTalkResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['created', 'started', 'done', 'error']),
  result_url: z.string().url().optional(),
  error: z.string().optional(),
  created_at: z.string(),
  started_at: z.string().optional(),
  finished_at: z.string().optional(),
});

export type DIDTalkResponse = z.infer<typeof DIDTalkResponseSchema>;

export class DIDClient {
  private config: DIDConfig;

  constructor(config: DIDConfig) {
    this.config = DIDConfigSchema.parse(config);
  }

  async createTalk(request: CreateTalkRequest): Promise<DIDTalkResponse> {
    const validated = CreateTalkRequestSchema.parse(request);

    const response = await fetch(`${this.config.baseUrl}/talks`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${btoa(this.config.apiKey)}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(validated),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`D-ID API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return DIDTalkResponseSchema.parse(data);
  }

  async getTalk(talkId: string): Promise<DIDTalkResponse> {
    const response = await fetch(`${this.config.baseUrl}/talks/${talkId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${btoa(this.config.apiKey)}`,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`D-ID API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return DIDTalkResponseSchema.parse(data);
  }

  async waitForCompletion(talkId: string, pollIntervalMs: number = 5000, maxAttempts: number = 60): Promise<DIDTalkResponse> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const talk = await this.getTalk(talkId);

      if (talk.status === 'done') {
        return talk;
      }

      if (talk.status === 'error') {
        throw new Error(`D-ID talk failed: ${talk.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, pollIntervalMs));
    }

    throw new Error('D-ID talk timed out');
  }
}

export function createDIDClient(env: { DID_API_KEY: string; DID_BASE_URL?: string }): DIDClient {
  return new DIDClient({
    apiKey: env.DID_API_KEY,
    baseUrl: env.DID_BASE_URL || 'https://api.d-id.com',
  });
}