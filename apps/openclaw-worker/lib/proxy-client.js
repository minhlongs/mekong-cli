/**
 * Proxy Client — Unified LLM call via AG Proxy (Anthropic /v1/messages format)
 * 
 * FIX 2026-02-19: AG Proxy uses Anthropic API format (/v1/messages), NOT OpenAI (/v1/chat/completions).
 * FIX 2026-02-21: Added retry with backoff + detailed error logging (AGI Enhancement Fix #1).
 * 
 * Usage:
 *   const { callLLM } = require('./proxy-client');
 *   const text = await callLLM({ system: '...', user: '...', maxTokens: 200 });
 */

const fs = require('fs');
const config = require('../config');

const PROXY_URL = `${config.CLOUD_BRAIN_URL || 'http://127.0.0.1:20128'}/v1/messages`;
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 2000;

function log(msg) {
    const ts = new Date().toISOString().slice(11, 19);
    const line = `[${ts}] [proxy-client] ${msg}\n`;
    try { fs.appendFileSync(config.LOG_FILE, line); } catch (_) { }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Call LLM via AG Proxy using Anthropic /v1/messages format
 * Retries up to MAX_RETRIES times with RETRY_DELAY_MS backoff.
 * 
 * @param {{ system?: string, user: string, model?: string, maxTokens?: number, temperature?: number, timeoutMs?: number }} opts
 * @returns {Promise<string|null>} - Response text or null on error
 */
async function callLLM({ system, user, model, maxTokens = 200, temperature = 0, timeoutMs = 15000 }) {
    const messages = [{ role: 'user', content: user }];

    const payload = {
        model: model || config.FALLBACK_MODEL_NAME || 'gemini-3-flash',
        messages,
        max_tokens: maxTokens,
        temperature,
    };

    if (system) {
        payload.system = system;
    }

    let lastError = null;

    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {
            const response = await fetch(PROXY_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'ollama',
                    'anthropic-version': '2023-06-01',
                },
                body: JSON.stringify(payload),
                signal: AbortSignal.timeout(timeoutMs),
            });

            if (!response.ok) {
                const body = await response.text().catch(() => '(no body)');
                log(`WARN: LLM call failed (attempt ${attempt}/${MAX_RETRIES}) — HTTP ${response.status}: ${body.slice(0, 200)}`);
                lastError = `HTTP ${response.status}`;
                if (attempt < MAX_RETRIES) {
                    await sleep(RETRY_DELAY_MS * attempt);
                    continue;
                }
                return null;
            }

            const data = await response.json();
            const text = data?.content?.[0]?.text?.trim() || '';
            if (text) {
                if (attempt > 1) log(`OK: LLM call succeeded on attempt ${attempt}`);
                return text;
            }

            log(`WARN: LLM returned empty content (attempt ${attempt}/${MAX_RETRIES})`);
            lastError = 'empty_response';
            if (attempt < MAX_RETRIES) {
                await sleep(RETRY_DELAY_MS);
                continue;
            }
            return null;

        } catch (err) {
            const isTimeout = err.name === 'TimeoutError' || err.code === 'ABORT_ERR';
            const errType = isTimeout ? 'TIMEOUT' : err.code || err.name || 'UNKNOWN';
            log(`WARN: LLM call error (attempt ${attempt}/${MAX_RETRIES}) — ${errType}: ${err.message}`);
            lastError = errType;
            if (attempt < MAX_RETRIES) {
                await sleep(RETRY_DELAY_MS * attempt);
                continue;
            }
        }
    }

    log(`ERROR: All ${MAX_RETRIES} LLM call attempts failed. Last error: ${lastError}`);
    return null;
}

module.exports = { callLLM, PROXY_URL };
