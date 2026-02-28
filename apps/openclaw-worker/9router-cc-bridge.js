const express = require('express');
const app = express();
const PORT = 20129;
const TARGET_9ROUTER = 'http://127.0.0.1:11436';

app.use(express.json({ limit: '50mb' }));

app.get('/v1/users/me', (req, res) => {
    res.json({
        type: 'user',
        id: 'user_fake123',
        email: 'openclaw@antigravity.local',
        name: 'OpenClaw Bypass',
        account: {
            type: 'account',
            id: 'account_fake123',
            name: 'Antigravity Workspace'
        }
    });
});

app.get('/v1/models', (req, res) => {
    res.json({
        data: [
            { type: 'model', id: 'claude-3-5-sonnet-20241022', display_name: 'Claude 3.5 Sonnet (Flywheel Working)', created_at: new Date().toISOString() },
            { type: 'model', id: 'claude-3-opus-20240229', display_name: 'Claude 3 Opus (Flywheel Strategic)', created_at: new Date().toISOString() },
            { type: 'model', id: 'claude-sonnet-4-6-20250514', display_name: 'Claude Sonnet 4.6 (OpenFang API)', created_at: new Date().toISOString() },
            { type: 'model', id: 'claude-opus-4-5-20250514', display_name: 'Claude Opus 4.5 (OpenFang Pro)', created_at: new Date().toISOString() }
        ],
        has_more: false
    });
});

app.post('/v1/messages', async (req, res) => {
    try {
        const response = await fetch(`${TARGET_9ROUTER}/v1/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': 'ollama',
                'anthropic-version': req.headers['anthropic-version'] || '2023-06-01'
            },
            body: JSON.stringify(req.body)
        });

        const data = await response.json();
        res.status(response.status).json(data);
    } catch (e) {
        console.error('Bridge error:', e);
        res.status(500).json({ error: { type: 'api_error', message: e.message } });
    }
});

app.listen(PORT, () => {
    console.log(`🦞 9Router CC CLI Bridge running on http://127.0.0.1:${PORT}`);
});
