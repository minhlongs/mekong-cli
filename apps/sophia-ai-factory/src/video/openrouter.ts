import { z } from 'zod';

export const OpenRouterConfigSchema = z.object({
  apiKey: z.string().min(1),
  baseUrl: z.string().url().default('https://openrouter.ai/api/v1'),
  siteUrl: z.string().url().optional(),
  siteName: z.string().optional(),
});

export type OpenRouterConfig = z.infer<typeof OpenRouterConfigSchema>;

export const ChatMessageSchema = z.object({
  role: z.enum(['system', 'user', 'assistant']),
  content: z.string(),
});

export type ChatMessage = z.infer<typeof ChatMessageSchema>;

export const ChatCompletionRequestSchema = z.object({
  model: z.string().min(1),
  messages: z.array(ChatMessageSchema).min(1),
  temperature: z.number().min(0).max(2).default(0.7),
  max_tokens: z.number().min(1).max(8192).optional(),
  top_p: z.number().min(0).max(1).default(1),
  frequency_penalty: z.number().min(-2).max(2).default(0),
  presence_penalty: z.number().min(-2).max(2).default(0),
});

export type ChatCompletionRequest = z.infer<typeof ChatCompletionRequestSchema>;

export const ChatCompletionChoiceSchema = z.object({
  index: z.number(),
  message: ChatMessageSchema,
  finish_reason: z.enum(['stop', 'length', 'tool_calls', 'content_filter', 'function_call']),
});

export type ChatCompletionChoice = z.infer<typeof ChatCompletionChoiceSchema>;

export const ChatCompletionResponseSchema = z.object({
  id: z.string(),
  object: z.literal('chat.completion'),
  created: z.number(),
  model: z.string(),
  choices: z.array(ChatCompletionChoiceSchema),
  usage: z.object({
    prompt_tokens: z.number(),
    completion_tokens: z.number(),
    total_tokens: z.number(),
  }).optional(),
});

export type ChatCompletionResponse = z.infer<typeof ChatCompletionResponseSchema>;

export const ScriptGenerationRequestSchema = z.object({
  topic: z.string().min(1).max(500),
  duration_seconds: z.number().min(5).max(300),
  language: z.enum(['en', 'vi']).default('en'),
  tone: z.enum(['professional', 'casual', 'energetic', 'educational']).default('professional'),
  target_audience: z.string().optional(),
  key_points: z.array(z.string()).max(5).optional(),
});

export type ScriptGenerationRequest = z.infer<typeof ScriptGenerationRequestSchema>;

export const GeneratedScriptSchema = z.object({
  title: z.string(),
  scenes: z.array(z.object({
    text: z.string(),
    duration_estimate: z.number(),
    visual_cue: z.string().optional(),
  })),
  total_duration_estimate: z.number(),
  word_count: z.number(),
});

export type GeneratedScript = z.infer<typeof GeneratedScriptSchema>;

export const GeneratedScriptOptionalSchema = GeneratedScriptSchema.optional();

export class OpenRouterClient {
  private config: OpenRouterConfig;

  constructor(config: OpenRouterConfig) {
    this.config = OpenRouterConfigSchema.parse(config);
  }

  async chatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const validated = ChatCompletionRequestSchema.parse(request);

    const headers: Record<string, string> = {
      'Authorization': `Bearer ${this.config.apiKey}`,
      'Content-Type': 'application/json',
    };

    if (this.config.siteUrl) {
      headers['HTTP-Referer'] = this.config.siteUrl;
    }
    if (this.config.siteName) {
      headers['X-Title'] = this.config.siteName;
    }

    const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(validated),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`OpenRouter API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    return ChatCompletionResponseSchema.parse(data);
  }

  async generateScript(request: ScriptGenerationRequest): Promise<GeneratedScript> {
    const validated = ScriptGenerationRequestSchema.parse(request);

    const systemPrompt = `You are an expert video script writer. Generate a compelling video script for an AI avatar presenter.
Language: ${validated.language === 'vi' ? 'Vietnamese' : 'English'}
Tone: ${validated.tone}
Target duration: ${validated.duration_seconds} seconds
${validated.target_audience ? `Target audience: ${validated.target_audience}` : ''}
${validated.key_points?.length ? `Key points to cover: ${validated.key_points.join(', ')}` : ''}

Return ONLY a JSON object with this exact structure:
{
  "title": "string",
  "scenes": [
    {"text": "string", "duration_estimate": number, "visual_cue": "string (optional)"}
  ],
  "total_duration_estimate": number,
  "word_count": number
}

Each scene text should be 1-3 sentences. Total scenes: 3-6.`;

    const completion = await this.chatCompletion({
      model: 'anthropic/claude-3.5-sonnet',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: `Topic: ${validated.topic}` },
      ],
      temperature: 0.7,
      top_p: 1,
      frequency_penalty: 0,
      presence_penalty: 0,
      max_tokens: 2000,
    });

    const content = completion.choices[0]?.message.content;
    if (!content) {
      throw new Error('OpenRouter returned empty response');
    }

    try {
      const parsed = JSON.parse(content);
      return GeneratedScriptSchema.parse(parsed);
    } catch (e) {
      throw new Error(`Failed to parse script: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  }
}

export function createOpenRouterClient(env: {
  OPENROUTER_API_KEY: string;
  OPENROUTER_BASE_URL?: string;
  OPENROUTER_SITE_URL?: string;
  OPENROUTER_SITE_NAME?: string;
}): OpenRouterClient {
  return new OpenRouterClient({
    apiKey: env.OPENROUTER_API_KEY,
    baseUrl: env.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
    siteUrl: env.OPENROUTER_SITE_URL,
    siteName: env.OPENROUTER_SITE_NAME,
  });
}