import { z } from 'zod';
import { DIDClient, createDIDClient, CreateTalkRequest, DIDTalkResponse } from './did';
import { ElevenLabsClient, createElevenLabsClient, TextToSpeechRequest } from './elevenlabs';
import { OpenRouterClient, createOpenRouterClient, ScriptGenerationRequest, GeneratedScript, GeneratedScriptSchema } from './openrouter';

export const VideoPipelineConfigSchema = z.object({
  didApiKey: z.string().min(1),
  didBaseUrl: z.string().url().optional(),
  elevenlabsApiKey: z.string().min(1),
  elevenlabsBaseUrl: z.string().url().optional(),
  openrouterApiKey: z.string().min(1),
  openrouterBaseUrl: z.string().url().optional(),
  openrouterSiteUrl: z.string().url().optional(),
  openrouterSiteName: z.string().optional(),
  defaultAvatarUrl: z.string().url(),
  defaultVoiceId: z.string().min(1),
});

export type VideoPipelineConfig = z.infer<typeof VideoPipelineConfigSchema>;

export const VideoJobStatusSchema = z.enum([
  'pending',
  'script_generating',
  'script_ready',
  'tts_generating',
  'tts_ready',
  'video_generating',
  'completed',
  'failed',
]);

export type VideoJobStatus = z.infer<typeof VideoJobStatusSchema>;

export const VideoJobSchema = z.object({
  id: z.string(),
  userId: z.string(),
  status: VideoJobStatusSchema,
  topic: z.string(),
  durationSeconds: z.number().positive(),
  language: z.enum(['en', 'vi']).default('en'),
  tone: z.enum(['professional', 'casual', 'energetic', 'educational']).default('professional'),
  targetAudience: z.string().optional(),
  keyPoints: z.array(z.string()).optional(),
  script: GeneratedScriptSchema.optional(),
  audioUrl: z.string().url().optional(),
  videoUrl: z.string().url().optional(),
  error: z.string().optional(),
  progress: z.number().min(0).max(100).default(0),
  createdAt: z.number(),
  updatedAt: z.number(),
  completedAt: z.number().optional(),
  webhookUrl: z.string().url().optional(),
  mcuCreditsCharged: z.number().default(0),
});

export type VideoJob = z.infer<typeof VideoJobSchema>;

export const CreateVideoJobRequestSchema = z.object({
  userId: z.string(),
  topic: z.string().min(1).max(500),
  durationSeconds: z.number().min(5).max(300),
  language: z.enum(['en', 'vi']).default('en'),
  tone: z.enum(['professional', 'casual', 'energetic', 'educational']).default('professional'),
  targetAudience: z.string().optional(),
  keyPoints: z.array(z.string()).max(5).optional(),
  webhookUrl: z.string().url().optional(),
  avatarUrl: z.string().url().optional(),
  voiceId: z.string().optional(),
});

export type CreateVideoJobRequest = z.infer<typeof CreateVideoJobRequestSchema>;

export class VideoPipeline {
  private state: DurableObjectState;
  private config: VideoPipelineConfig;
  private didClient: DIDClient;
  private elevenlabsClient: ElevenLabsClient;
  private openrouterClient: OpenRouterClient;

  constructor(state: DurableObjectState, env: VideoPipelineConfig) {
    this.state = state;
    this.config = VideoPipelineConfigSchema.parse(env);

    this.didClient = createDIDClient({
      DID_API_KEY: this.config.didApiKey,
      DID_BASE_URL: this.config.didBaseUrl,
    });

    this.elevenlabsClient = createElevenLabsClient({
      ELEVENLABS_API_KEY: this.config.elevenlabsApiKey,
      ELEVENLABS_BASE_URL: this.config.elevenlabsBaseUrl,
    });

    this.openrouterClient = createOpenRouterClient({
      OPENROUTER_API_KEY: this.config.openrouterApiKey,
      OPENROUTER_BASE_URL: this.config.openrouterBaseUrl,
      OPENROUTER_SITE_URL: this.config.openrouterSiteUrl,
      OPENROUTER_SITE_NAME: this.config.openrouterSiteName,
    });
  }

  async createJob(request: CreateVideoJobRequest): Promise<VideoJob> {
    const validated = CreateVideoJobRequestSchema.parse(request);

    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const now = Date.now();

    const job: VideoJob = {
      id: jobId,
      userId: validated.userId,
      status: 'pending',
      topic: validated.topic,
      durationSeconds: validated.durationSeconds,
      language: validated.language,
      tone: validated.tone,
      targetAudience: validated.targetAudience,
      keyPoints: validated.keyPoints,
      progress: 0,
      createdAt: now,
      updatedAt: now,
      webhookUrl: validated.webhookUrl,
      mcuCreditsCharged: 0,
    };

    await this.state.storage.put(`job:${jobId}`, job);

    // Start pipeline asynchronously
    this.executePipeline(jobId, validated.avatarUrl || this.config.defaultAvatarUrl, validated.voiceId || this.config.defaultVoiceId)
      .catch(err => this.handleJobError(jobId, err));

    return job;
  }

  async getJob(jobId: string): Promise<VideoJob | null> {
    const job = await this.state.storage.get<VideoJob>(`job:${jobId}`);
    return job ? VideoJobSchema.parse(job) : null;
  }

  async getUserJobs(userId: string, limit: number = 50): Promise<VideoJob[]> {
    const jobs: VideoJob[] = [];
    const allItems = await this.state.storage.list();
    for (const [key, value] of allItems) {
      if (key.startsWith('job:') && (value as any).userId === userId) {
        jobs.push(VideoJobSchema.parse(value));
      }
    }
    return jobs
      .sort((a, b) => b.createdAt - a.createdAt)
      .slice(0, limit);
  }

  private async executePipeline(jobId: string, avatarUrl: string, voiceId: string): Promise<void> {
    let job = await this.getJob(jobId);
    if (!job) throw new Error('Job not found');

    try {
      // Step 1: Generate script
      await this.updateJob(jobId, { status: 'script_generating', progress: 10 });
      job = (await this.getJob(jobId))!;

      const scriptRequest: ScriptGenerationRequest = {
        topic: job.topic,
        duration_seconds: job.durationSeconds,
        language: job.language,
        tone: job.tone,
        target_audience: job.targetAudience,
        key_points: job.keyPoints,
      };

      const script = await this.openrouterClient.generateScript(scriptRequest);
      await this.updateJob(jobId, { status: 'script_ready', script, progress: 30 });
      job = (await this.getJob(jobId))!;

      // Step 2: Generate TTS audio for each scene
      await this.updateJob(jobId, { status: 'tts_generating', progress: 40 });
      job = (await this.getJob(jobId))!;

      const fullText = job.script!.scenes.map(s => s.text).join(' ');
      const ttsRequest: TextToSpeechRequest = {
        text: fullText,
        voice_id: voiceId,
        model_id: 'eleven_multilingual_v2',
      };

      const audioBuffer = await this.elevenlabsClient.textToSpeech(ttsRequest);

      // In production, upload to R2/S3 and get URL
      // For now, we'll simulate with a placeholder
      const audioUrl = `https://storage.example.com/audio/${jobId}.mp3`;
      await this.updateJob(jobId, { status: 'tts_ready', audioUrl, progress: 60 });
      job = (await this.getJob(jobId))!;

      // Step 3: Generate video with D-ID
      await this.updateJob(jobId, { status: 'video_generating', progress: 70 });
      job = (await this.getJob(jobId))!;

      const talkRequest: CreateTalkRequest = {
        script: {
          type: 'text',
          input: fullText,
          provider: {
            type: 'microsoft',
          },
        },
        source_url: avatarUrl,
      };

      const talk = await this.didClient.createTalk(talkRequest);
      const completedTalk = await this.didClient.waitForCompletion(talk.id);

      if (!completedTalk.result_url) {
        throw new Error('D-ID video generation failed - no result URL');
      }

      await this.updateJob(jobId, {
        status: 'completed',
        videoUrl: completedTalk.result_url,
        progress: 100,
        completedAt: Date.now(),
        mcuCreditsCharged: job.durationSeconds,
      });

      // Fire webhook if configured
      if (job.webhookUrl) {
        await this.fireWebhook(job.webhookUrl, jobId, 'completed', { videoUrl: completedTalk.result_url });
      }

    } catch (error) {
      await this.handleJobError(jobId, error);
    }
  }

  private async updateJob(jobId: string, updates: Partial<VideoJob>): Promise<void> {
    const job = await this.getJob(jobId);
    if (!job) throw new Error('Job not found');

    const updated: VideoJob = {
      ...job,
      ...updates,
      updatedAt: Date.now(),
    };

    await this.state.storage.put(`job:${jobId}`, updated);
  }

  private async handleJobError(jobId: string, error: unknown): Promise<void> {
    const message = error instanceof Error ? error.message : 'Unknown error';
    await this.updateJob(jobId, {
      status: 'failed',
      error: message,
      progress: 0,
      updatedAt: Date.now(),
    });

    const job = await this.getJob(jobId);
    if (job?.webhookUrl) {
      await this.fireWebhook(job.webhookUrl, jobId, 'failed', { error: message });
    }
  }

  private async fireWebhook(url: string, jobId: string, status: string, data: Record<string, unknown>): Promise<void> {
    try {
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jobId, status, data, timestamp: Date.now() }),
      });
    } catch (e) {
      console.error('Webhook failed:', e);
    }
  }
}

export function createVideoPipelineDO(state: DurableObjectState, env: VideoPipelineConfig): VideoPipeline {
  return new VideoPipeline(state, env);
}