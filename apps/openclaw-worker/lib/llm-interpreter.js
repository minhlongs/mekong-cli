/**
 * LLM Interpreter — CTO Vision via Antigravity Proxy (9router)
 * AGI Level 7: Hardened LLM-powered state detection
 *
 * 📜 Binh Pháp Ch.1 始計: 「知己知彼，百戰不殆」
 *    "Know yourself and know the enemy, and you will never be defeated"
 *
 * Gives the CTO "eyes" by sending CC CLI's tmux output to gemini-3-flash
 * for intelligent state detection. Replaces fragile regex-based detection.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const config = require('../config');

const PROXY_PORT = config.PROXY_PORT || 20128;
const MODEL = 'gemini-3-flash';
const TIMEOUT_MS = 15000;
const CACHE_TTL_MS = 8000;
const METRICS_FILE = path.join(config.MEKONG_DIR, 'apps/openclaw-worker/data/llm-metrics.json');

// Ensure data dir exists
const DATA_DIR = path.dirname(METRICS_FILE);
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// Simple in-memory cache
let _cache = { result: null, timestamp: 0 };

// Metrics tracking
let _metrics = { calls: 0, successes: 0, failures: 0, avgLatencyMs: 0, totalLatencyMs: 0 };

function log(msg) {
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false });
    const line = `[${ts}] [tom-hum] [LLM-VISION] ${msg}`;
    try { fs.appendFileSync('/Users/macbookprom1/tom_hum_cto.log', line + '\n'); } catch (e) { }
}

function saveMetrics() {
    try { fs.writeFileSync(METRICS_FILE, JSON.stringify(_metrics, null, 2)); } catch (e) { }
}

const SYSTEM_PROMPT = `You are a CTO monitoring agent. Analyze Claude Code CLI terminal output and return state JSON.

RULES:
- Return ONLY valid JSON, no markdown fences, no explanation
- The prompt symbol is "❯" — if it's at the bottom with nothing after it → IDLE
- Status words (Thinking, Orbiting, Cooking, Churning, Sautéing, etc.) → BUSY
- "Cooked for Xm Ys" or "Churned for Xm Ys" or "Brewed for Xs" → COMPLETE
- "Interrupted" → IDLE (was stopped)
- Stack traces, errors, "Background task failed" → ERROR
- Yes/No questions, approval prompts, "Press Enter to continue" (during compacting) → QUESTION
- "bypass permissions on" or "(shift+tab to cycle)" in the status bar → IGNORE (not a question)
- "Compacting conversation..." AND prompt "❯" is present → QUESTION (needs Enter to unblock)
- "Background tasks" view (with "esc to exit") → QUESTION (needs Escape to exit view)
- "Context limit reached - /compact or /clear to continue" → CONTEXT_LIMIT

Return: {"state":"busy|idle|complete|error|question|context_limit","confidence":0.9,"summary":"brief","lastAction":"what finished","recommendation":"next step"}`;

/**
 * Raw HTTP call to Antigravity Proxy
 */
function callLLM(prompt) {
    return new Promise(async (resolve) => {
        const body = JSON.stringify({
            model: MODEL,
            max_tokens: 1024,
            system: SYSTEM_PROMPT,
            messages: [{ role: 'user', content: prompt }]
        });

        const controller = new AbortController();
        const timer = setTimeout(() => {
            log(`TIMEOUT after ${TIMEOUT_MS}ms`);
            controller.abort();
        }, TIMEOUT_MS);

        try {
            const res = await fetch(`http://127.0.0.1:${PROXY_PORT}/v1/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'ollama',
                    'anthropic-version': '2023-06-01'
                },
                body: body,
                signal: controller.signal
            });
            clearTimeout(timer);

            const txt = await res.text();

            try {
                const response = JSON.parse(txt);

                const textBlock = Array.isArray(response.content)
                    ? response.content.find(c => c.type === 'text')
                    : { text: typeof response.content === 'string' ? response.content : '' };

                let text = textBlock?.text || '';

                if (!text && response.error) {
                    text = `{"state": "error", "summary": "${response.error.message}"}`;
                }

                if (!text) {
                    const types = Array.isArray(response.content) ? response.content.map(c => c.type).join(',') : typeof response.content;
                    log(`Empty text in response. Content types: ${types}. Raw: ${txt.slice(0, 100)}...`);
                    resolve(null);
                    return;
                }

                // Parse JSON (strip thought tags and markdown fences)
                const jsonStr = text
                    .replace(/<thought>[\s\S]*?<\/thought>/g, '') // Strip thinking blocks
                    .replace(/```json?\n?/g, '')
                    .replace(/```/g, '')
                    .trim();
                const result = JSON.parse(jsonStr);
                resolve(result);
            } catch (e) {
                log(`Parse error: ${e.message}. Raw: ${txt.slice(0, 200)}`);
                resolve(null);
            }
        } catch (e) {
            clearTimeout(timer);
            log(`HTTP/Fetch error: ${e.message}`);
            resolve(null);
        }
    });
}

/**
 * Interpret CC CLI state from tmux output.
 * Features: cache, retry, metrics, logging.
 */
async function interpretState(paneOutput) {
    // Check cache
    const now = Date.now();
    if (_cache.result && (now - _cache.timestamp) < CACHE_TTL_MS) {
        return _cache.result;
    }

    _metrics.calls++;
    const startTime = Date.now();

    // Truncate to last 40 lines to save tokens
    const lines = paneOutput.split('\n');
    const truncated = lines.slice(-40).join('\n');
    const prompt = `Analyze this CC CLI terminal output:\n\n${truncated}`;

    // Attempt 1
    let result = await callLLM(prompt);

    // Retry with simpler prompt if failed
    if (!result) {
        log(`Attempt 1 failed — retrying with simpler prompt`);
        const lastLines = lines.slice(-10).join('\n');
        const simplePrompt = `Terminal last 10 lines:\n${lastLines}\n\nReturn JSON with state (busy/idle/complete/error/question).`;
        result = await callLLM(simplePrompt);
    }

    const latencyMs = Date.now() - startTime;
    _metrics.totalLatencyMs += latencyMs;

    if (result) {
        _metrics.successes++;
        _metrics.avgLatencyMs = Math.round(_metrics.totalLatencyMs / _metrics.successes);
        // Validate and normalize
        if (!result.state) result.state = 'unknown';
        if (!result.confidence) result.confidence = 0.5;
        if (!result.summary) result.summary = '';
        if (!result.lastAction) result.lastAction = '';
        if (!result.recommendation) result.recommendation = '';

        log(`${result.state.toUpperCase()} (${result.confidence}) ${latencyMs}ms — ${result.summary.slice(0, 80)}`);
        _cache = { result, timestamp: Date.now() };
        saveMetrics();
        return result;
    }

    // Both attempts failed
    _metrics.failures++;
    _metrics.avgLatencyMs = _metrics.successes > 0 ? Math.round(_metrics.totalLatencyMs / _metrics.successes) : 0;
    saveMetrics();

    const fallback = {
        state: 'unknown', confidence: 0,
        summary: 'LLM call failed — falling back to regex',
        lastAction: '', recommendation: 'use_regex_fallback'
    };
    log(`FAILED (${latencyMs}ms) — both attempts failed. Calls: ${_metrics.calls}, Success: ${_metrics.successes}, Fail: ${_metrics.failures}`);
    return fallback;
}

/**
 * Generate a mission completion summary from CC CLI output.
 * Called after a mission completes to log what CC CLI actually did.
 */
async function getMissionSummary(paneOutput) {
    const lines = paneOutput.split('\n').slice(-50).join('\n');
    const prompt = `This CC CLI session just completed a mission. Analyze the output and return JSON:
{"filesChanged": 0, "bugsFixed": 0, "summary": "what was accomplished", "improvements": ["list of specific improvements"]}

Terminal output:
${lines}`;

    const result = await callLLM(prompt);
    if (result) {
        log(`MISSION SUMMARY: ${JSON.stringify(result).slice(0, 200)}`);
        // Save to mission summaries file
        try {
            const summariesFile = path.join(DATA_DIR, 'mission-summaries.json');
            let summaries = [];
            if (fs.existsSync(summariesFile)) summaries = JSON.parse(fs.readFileSync(summariesFile, 'utf-8'));
            summaries.push({ ...result, timestamp: new Date().toISOString() });
            // Keep last 100 summaries
            if (summaries.length > 100) summaries = summaries.slice(-100);
            fs.writeFileSync(summariesFile, JSON.stringify(summaries, null, 2));
        } catch (e) { }
    }
    return result;
}

/**
 * Ask LLM which strategic task to run next, given project health and history.
 */
async function selectNextTask(project, taskHistory, availableTasks) {
    const prompt = `You are a CTO deciding which improvement task to run next for project "${project}".

Task history (times run): ${JSON.stringify(taskHistory)}
Available tasks: ${JSON.stringify(availableTasks.map(t => ({ id: t.id, cmd: t.cmd.slice(0, 60) })))}

Pick the MOST valuable task to run next. Consider:
- Tasks run less often should be prioritized
- Diminishing returns for over-run tasks
- Balance security, performance, quality, and maintenance

Return: {"taskId": "chosen_task_id", "reason": "why this task"}`;

    const result = await callLLM(prompt);
    if (result?.taskId) {
        log(`TASK SELECTION: ${result.taskId} — ${result.reason?.slice(0, 80)}`);
    }
    return result;
}

function clearCache() {
    _cache = { result: null, timestamp: 0 };
}

function getMetrics() {
    return { ..._metrics };
}

module.exports = { interpretState, getMissionSummary, selectNextTask, clearCache, getMetrics };
