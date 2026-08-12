import { z } from 'zod';

export const ElevenLabsConfigSchema = z.object({
  apiKey: z.string().min(1),
  baseUrl: z.string().url().default('https://api.elevenlabs.io/v1'),
});

export type ElevenLabsConfig = z.infer<typeof ElevenLabsConfigSchema>;

export const TextToSpeechRequestSchema = z.object({
  text: z.string().min(1).max(5000),
  voice_id: z.string().min(1),
  model_id: z.string().default('eleven_multilingual_v2'),
  voice_settings: z.object({
    stability: z.number().min(0).max(1).default(0.5),
    similarity_boost: z.number().min(0).max(1).default(0.75),
    style: z.number().min(0).max(1).default(0),
    use_speaker_boost: z.boolean().default(true),
  }).optional(),
});

export type TextToSpeechRequest = z.infer<typeof TextToSpeechRequestSchema>;

export const VoiceSchema = z.object({
  voice_id: z.string(),
  name: z.string(),
  category: z.string(),
  description: z.string().optional(),
});

export type Voice = z.infer<typeof VoiceSchema>;

export class ElevenLabsClient {
  private config: ElevenLabsConfig;

  constructor(config: ElevenLabsConfig) {
    this.config = ElevenLabsConfigSchema.parse(config);
  }

  async textToSpeech(request: TextToSpeechRequest): Promise<ArrayBuffer> {
    const validated = TextToSpeechRequestSchema.parse(request);

    const response = await fetch(`${this.config.baseUrl}/text-to-speech/${validated.voice_id}`, {
      method: 'POST',
      headers: {
        'xi-api-key': this.config.apiKey,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg',
      },
      body: JSON.stringify({
        text: validated.text,
        model_id: validated.model_id,
        voice_settings: validated.voice_settings,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} - ${error}`);
    }

    return response.arrayBuffer();
  }

  async getVoices(): Promise<Voice[]> {
    const response = await fetch(`${this.config.baseUrl}/voices`, {
      method: 'GET',
      headers: {
        'xi-api-key': this.config.apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} - ${error}`);
    }

    const data: { voices: unknown[] } = await response.json();
    return z.array(VoiceSchema).parse(data.voices);
  }

  async getVoice(voiceId: string): Promise<Voice> {
    const response = await fetch(`${this.config.baseUrl}/voices/${voiceId}`, {
      method: 'GET',
      headers: {
        'xi-api-key': this.config.apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`ElevenLabs API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return VoiceSchema.parse(data);
  }
}

export function createElevenLabsClient(env: { ELEVENLABS_API_KEY: string; ELEVENLABS_BASE_URL?: string }): ElevenLabsClient {
  return new ElevenLabsClient({
    apiKey: env.ELEVENLABS_API_KEY,
    baseUrl: env.ELEVENLABS_BASE_URL || 'https://api.elevenlabs.io/v1',
  });
}