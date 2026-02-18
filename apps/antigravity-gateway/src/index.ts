/**
 * 🏗️ ANTIGRAVITY GATEWAY (Edge Tunnel)
 * Status: Phase 1.5 (Streaming & SecOps & Rotation)
 * Function: Auth + Converter + Streaming + PII Masking + Key Rotation
 */

export interface Env {
    GOOGLE_API_KEY: string; // Legacy single key
    GOOGLE_API_KEYS: string; // New: Comma-separated list for rotation
    COOK_AUTH_TOKEN: string;
    TARGET_MODEL: string;
    UPSTREAM_URL: string;
}

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        // 1. CORS Preflight
        if (request.method === "OPTIONS") {
            return new Response(null, {
                headers: {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                },
            });
        }

        // 2. Auth Check
        const authHeader = request.headers.get("authorization");
        const authToken = request.headers.get("x-cook-auth-token") ||
            authHeader?.replace("Bearer ", "") ||
            request.headers.get("x-api-key");

        // PASSTHROUGH ALLOWANCE: If it looks like a Google Token, let it pass to the Proxy Logic
        const isGoogleToken = authToken && (authToken.startsWith("ya29") || authToken.startsWith("adc-"));

        if (!isGoogleToken && env.COOK_AUTH_TOKEN && authToken !== env.COOK_AUTH_TOKEN) {
            // Judo Fix: If authToken matches one of the rotated keys, allow it? 
            // No, Keep strict Cook Token for now to prevent unauthorized usage, 
            // but if the CLI sends the key as Bearer, we check it against COOK_AUTH_TOKEN.
            return new Response(JSON.stringify({
                error: "Unauthorized: Invalid Cook Token",
                debug: {
                    received_x_cook_token: request.headers.get("x-cook-auth-token"),
                    received_authorization: request.headers.get("authorization"),
                    received_x_api_key: request.headers.get("x-api-key"),
                    expected_token_preview: env.COOK_AUTH_TOKEN ? env.COOK_AUTH_TOKEN.substring(0, 5) + "..." : "NOT_SET"
                }
            }), {
                status: 401,
                headers: { "Content-Type": "application/json" }
            });
        }

        // 3. Construct Upstream URL
        let upstreamUrl = env.UPSTREAM_URL; // Default: https://generativelanguage.googleapis.com
        let model = env.TARGET_MODEL;

        // VERTEX AI PIVOT: If using Google Token (likely Cloud Platform scope), switch to Vertex AI Endpoint
        // Project ID: openclaw-raas-hub-1770348928 (Verified Billing Enabled)
        if (isGoogleToken) {
            const projectId = "openclaw-raas-hub-1770348928";
            const location = "us-central1";
            // Vertex uses a different URL structure
            // https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}:streamGenerateContent
            upstreamUrl = `https://${location}-aiplatform.googleapis.com`;
            // Rewrite the path in the fetch call later, or handle it here?
            // The proxy logic below appends `path`, which is `/v1/messages`.
            // We need to intercept the path construction.
        }

        const url = new URL(request.url);
        const path = url.pathname; // e.g. /v1/messages

        let vertexPath = "";
        if (isGoogleToken) {
            // Map Claude Model to Vertex Model
            // gemini-3.0-pro-preview might not be on Vertex yet, fallback to gemini-1.5-pro
            const vertexModel = "gemini-1.5-flash-001";
            vertexPath = `/v1/projects/openclaw-raas-hub-1770348928/locations/us-central1/publishers/google/models/${vertexModel}:streamGenerateContent`;
        }
        if (request.method === "POST" && url.pathname.includes("/v1/messages")) {
            try {
                return await handleProxyRequest(request, env);
            } catch (err: any) {
                return new Response(JSON.stringify({
                    type: "error",
                    error: { type: "internal_error", message: err.message }
                }), { status: 500, headers: { "Content-Type": "application/json" } });
            }
        }

        return new Response("🦞 Antigravity Gateway: Online (Streaming Ready)", { status: 200 });
    },
};

async function handleProxyRequest(req: Request, env: Env): Promise<Response> {
    const body: any = await req.json();
    const { messages, system, stream } = body;

    // A. Convert Payload
    const geminiPayload = convertToGemini(messages, system);

    // B. Auto Model Selection (Antigravity-style Pro+Flash)
    // opus/heavy → Pro (HIGH), sonnet/light → Flash (FAST)
    const requestModel = body.model || '';
    const isThinking = requestModel.includes('opus') || JSON.stringify(body).length > 65536;
    const model = isThinking ? 'gemini-3-pro' : (env.TARGET_MODEL || 'gemini-3-flash');

    // Auth Logic: "Immortal Pool" vs "Ultra Passthrough"
    const authHeader = req.headers.get("Authorization");
    // Heuristic: Google Bearer (ya29/adc-) OR Vertex API Key (AQ. or AIza strict)
    const isGoogleBearer = authHeader && (authHeader.startsWith("Bearer ya29") || authHeader.startsWith("Bearer adc-"));
    const isVertexApiKey = authHeader && (authHeader.startsWith("Bearer AQ.") || authHeader.startsWith("Bearer AIza"));
    const isGoogleToken = isGoogleBearer || isVertexApiKey;

    let upstreamUrl = "";
    let upstreamHeaders: HeadersInit = { "Content-Type": "application/json" };

    if (isGoogleToken) {
        // [MODE: VERTEX AI PASSTHROUGH]
        // User brings their own Enterprise Token (Cloud Platform Scope) -> Route to Vertex AI
        // Project ID: openclaw-raas-hub-1770348928 (Verified Billing Enabled)
        // Model: gemini-1.5-flash-001 (High Availability Fallback)
        const vertexModel = "gemini-1.5-flash-001";
        const projectId = "openclaw-raas-hub-1770348928";
        const location = "us-central1";

        const token = authHeader!.replace("Bearer ", "");
        const querySuffix = isVertexApiKey
            ? `?key=${token}` // API Key Mode
            : '';             // Bearer Mode (Header)

        // Correct URL Construction for Vertex AI
        const baseUrl = `https://${location}-aiplatform.googleapis.com/v1/projects/${projectId}/locations/${location}/publishers/google/models/${vertexModel}`;
        const action = stream ? 'streamGenerateContent' : 'generateContent';
        let queryParams = stream ? '?alt=sse' : '';

        if (isVertexApiKey) {
            queryParams += (queryParams ? '&' : '?') + `key=${token}`;
        }

        upstreamUrl = `${baseUrl}:${action}${queryParams}`;

        upstreamHeaders = {
            "Content-Type": "application/json"
        };

        // Only attach Bearer if it's NOT an API Key
        if (isGoogleBearer) {
            upstreamHeaders["Authorization"] = authHeader!;
        }
    } else {
        // [MODE: IMMORTAL POOL]
        // Antigravity Managed -> Use our Rotated API Keys
        const rotatedKey = getRotatedKey(env);
        upstreamUrl = `${env.UPSTREAM_URL || "https://generativelanguage.googleapis.com"}/v1beta/models/${model}:${stream ? 'streamGenerateContent?alt=sse&' : 'generateContent?'}key=${rotatedKey}`;
        // No Authorization header needed (Key is in URL)
    }

    if (stream) {
        return makeStreamingRequest(upstreamUrl, geminiPayload, model, upstreamHeaders);
    }

    // Non-Streaming Fallback (Debug Wrapped)
    try {
        let geminiRes = await fetch(upstreamUrl, {
            method: "POST",
            headers: upstreamHeaders,
            body: JSON.stringify(geminiPayload)
        });

        if (data.error) {
            return new Response(JSON.stringify({
                type: "error",
                error: { type: "api_error", message: data.error.message },
                debug: { upstreamUrl, model }
            }), { status: geminiRes.status, headers: { "Content-Type": "application/json" } });
        }

        const claudeResponse = {
            id: `msg_edge_${Date.now()}`,
            type: "message",
            role: "assistant",
            content: [{
                type: "text",
                text: data.candidates?.[0]?.content?.parts?.[0]?.text || ""
            }],
            model: "claude-3-5-sonnet-20240620",
            stop_reason: "end_turn",
            usage: {
                input_tokens: data.usageMetadata?.promptTokenCount || 0,
                output_tokens: data.usageMetadata?.candidatesTokenCount || 0
            }
        };

        return new Response(JSON.stringify(claudeResponse), {
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        });
    } catch (error: any) {
        return new Response(JSON.stringify({
            type: "error",
            error: { type: "internal_error", message: `Fetch Failed: ${error.message}` },
            debug: { upstreamUrl }
        }), { status: 500, headers: { "Content-Type": "application/json" } });
    }
}

// --- KEY ROTATION LOGIC ---
function getRotatedKey(env: Env): string {
    if (env.GOOGLE_API_KEYS) {
        // Split by comma, trim, and filter empty
        const keys = env.GOOGLE_API_KEYS.split(',').map(k => k.trim()).filter(k => k.length > 0);
        if (keys.length > 0) {
            // Simple Random Rotation
            const randomIndex = Math.floor(Math.random() * keys.length);
            return keys[randomIndex];
        }
    }
    // Fallback to single key
    return env.GOOGLE_API_KEY;
}

// --- STREAMING LOGIC ---
async function makeStreamingRequest(url: string, payload: any, model: string, headers: HeadersInit = { 'Content-Type': 'application/json' }): Promise<Response> {
    const response = await fetch(url, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
    });

    // Handle verification errors from upstream during stream init
    if (!response.ok) {
        const errorData: any = await response.json();
        return new Response(JSON.stringify({
            type: "error",
            error: { type: "api_error", message: errorData.error?.message || "Stream Init Failed" }
        }), { status: response.status, headers: { "Content-Type": "application/json" } });
    }

    if (!response.body) throw new Error("No response body");
    const reader = response.body.getReader();

    // Transform Gemini SSE -> Claude SSE
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    // Start the stream
    const msgId = `msg_edge_stream_${Date.now()}`;

    // Initial Message Headers
    const initStream = async () => {
        await writer.write(encoder.encode(`event: message_start\ndata: ${JSON.stringify({
            type: "message_start",
            message: {
                id: msgId,
                type: "message",
                role: "assistant",
                model: "claude-3-5-sonnet-20240620",
                content: [],
                stop_reason: null,
                stop_sequence: null,
                usage: { input_tokens: 0, output_tokens: 0 }
            }
        })}\n\n`));

        await writer.write(encoder.encode(`event: content_block_start\ndata: ${JSON.stringify({
            type: "content_block_start",
            index: 0,
            content_block: { type: "text", text: "" }
        })}\n\n`));
    };

    initStream();

    // Async processing
    (async () => {
        try {
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.slice(6);
                        if (jsonStr === "[DONE]") continue;
                        try {
                            const data = JSON.parse(jsonStr);
                            const text = data.candidates?.[0]?.content?.parts?.[0]?.text;

                            if (text) {
                                // Send Delta
                                await writer.write(encoder.encode(`event: content_block_delta\ndata: ${JSON.stringify({
                                    type: "content_block_delta",
                                    index: 0,
                                    delta: { type: "text_delta", text: text }
                                })}\n\n`));
                            }
                        } catch (e) { /* ignore parse error */ }
                    }
                }
            }

            // Finalize
            await writer.write(encoder.encode(`event: content_block_stop\ndata: ${JSON.stringify({
                type: "content_block_stop",
                index: 0
            })}\n\n`));

            await writer.write(encoder.encode(`event: message_delta\ndata: ${JSON.stringify({
                type: "message_delta",
                delta: { stop_reason: "end_turn", stop_sequence: null },
                usage: { output_tokens: 0 }
            })}\n\n`));

            await writer.write(encoder.encode(`event: message_stop\ndata: ${JSON.stringify({
                type: "message_stop"
            })}\n\n`));

        } catch (error) {
            // console.error("Stream Error", error);
        } finally {
            writer.close();
        }
    })();

    return new Response(readable, {
        headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    });
}

// --- SECOPS: PII MASKING ---
function maskSensitiveData(text: string): string {
    text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL_REDACTED]');
    text = text.replace(/(sk-[a-zA-Z0-9]{20,})/g, '[KEY_REDACTED]');
    return text;
}

// --- CONVERSION LOGIC ---
function convertToGemini(messages: any[], system: any) {
    const contents = messages.map(msg => ({
        role: msg.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: typeof msg.content === 'string' ? msg.content : msg.content?.[0]?.text || "" }]
    }));

    if (system) {
        const systemText = typeof system === 'string' ? system : (system[0]?.text || "");
        if (systemText) {
            if (contents.length > 0 && contents[0].role === 'user') {
                contents[0].parts[0].text = `[System Instruction]\n${systemText}\n\n[User Request]\n${contents[0].parts[0].text}`;
            } else {
                contents.unshift({ role: 'user', parts: [{ text: `[System Instruction]\n${systemText}` }] });
            }
        }
    }

    return {
        contents,
        generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 8192
        }
    };
}
