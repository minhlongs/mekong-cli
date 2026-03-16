const https = require('https');
const fs = require('fs');
const path = require('path');

const BYTEPLUS_API_KEY = process.env.BYTEPLUS_API_KEY || '5cee0d73-2a72-4f29-b001-c19f3e1c32ba';
const API_HOSTNAME = 'open.volcengineapi.com';
const API_PATH = '/api/v3/chat/completions';
const MODEL_NAME = 'doubao-pro-32k';

const args = process.argv.slice(2);
const project = args[0] || 'Unknown Project';
const stateFile = args[1];

let output = '';
if (stateFile && fs.existsSync(stateFile)) {
    output = fs.readFileSync(stateFile, 'utf-8');
}

// 🧠 MEMORY: Check which algorithm files already exist in the project
const PROJECT_DIR = path.join(process.env.HOME || '', `mekong-cli/apps/${project}`);
let existingAlgos = [];
try {
    const algoDir = path.join(PROJECT_DIR, 'src/algorithms');
    if (fs.existsSync(algoDir)) {
        existingAlgos = fs.readdirSync(algoDir).filter(f => f.endsWith('.ts') || f.endsWith('.py'));
    }
} catch (e) {}

// RaaS Algorithm commands — must produce REAL CODE
const ALL_CMDS = [
  '/cook Implement a scoring algorithm. Write TypeScript to src/algorithms/scoring-engine.ts',
  '/cook Implement a pricing engine. Write TypeScript to src/algorithms/pricing-engine.ts',
  '/cook Implement a recommendation algorithm. Write TypeScript to src/algorithms/recommendation-engine.ts',
  '/cook Implement a customer health scoring system. Write TypeScript to src/algorithms/health-score.ts',
  '/cook Implement a lead qualification algorithm. Write TypeScript to src/algorithms/lead-qualifier.ts',
  '/cook Build a revenue forecasting model. Write TypeScript to src/algorithms/revenue-forecast.ts',
  '/cook Build a competitive moat analyzer. Write TypeScript to src/algorithms/moat-analyzer.ts',
  '/cook Build a unit economics calculator. Write TypeScript to src/algorithms/unit-economics.ts',
  '/cook Build an A/B test statistical engine. Write TypeScript to src/algorithms/ab-test-engine.ts',
  '/cook Build a feature prioritization algorithm. Write TypeScript to src/algorithms/feature-prioritizer.ts',
];

// Filter out algorithms that already exist
const algoFileMap = {
    'scoring-engine.ts': 0,
    'pricing-engine.ts': 1,
    'recommendation-engine.ts': 2,
    'health-score.ts': 3,
    'lead-qualifier.ts': 4,
    'revenue-forecast.ts': 5,
    'moat-analyzer.ts': 6,
    'unit-economics.ts': 7,
    'ab-test-engine.ts': 8,
    'feature-prioritizer.ts': 9,
};

const availableCmds = ALL_CMDS.filter((_, i) => {
    const file = Object.keys(algoFileMap).find(k => algoFileMap[k] === i);
    return !existingAlgos.includes(file);
});

// If all algorithms exist, fallback to improvement commands
const cmdsToUse = availableCmds.length > 0 ? availableCmds : ALL_CMDS;

const prompt = `You are a Senior CTO AI managing the "${project}" RaaS factory.

TERMINAL OUTPUT:
\`\`\`
${output.slice(-1200)}
\`\`\`

EXISTING ALGORITHM FILES (ALREADY BUILT — DO NOT REBUILD):
${existingAlgos.length > 0 ? existingAlgos.join(', ') : 'None yet'}

AVAILABLE COMMANDS (pick ONE that creates a NEW algorithm):
${cmdsToUse.map((c, i) => `${i + 1}. ${c}`).join('\n')}

Pick the command that will generate the HIGHEST VALUE new algorithm that does NOT already exist.
Reply with ONLY the exact command string. No quotes, no explanation, no number prefix.`;

const payload = JSON.stringify({
    model: MODEL_NAME,
    messages: [
        { role: 'system', content: 'You are a CTO AI. Output only valid /cook commands. Never explain.' },
        { role: 'user', content: prompt }
    ],
    max_tokens: 100,
    temperature: 0.2
});

const req = https.request({
    hostname: API_HOSTNAME,
    path: API_PATH,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${BYTEPLUS_API_KEY}`,
        'Content-Length': Buffer.byteLength(payload)
    },
    timeout: 8000
}, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        try {
            const json = JSON.parse(data);
            if (json.error || !json.choices || !json.choices[0]) {
                process.exit(1);
            }
            let reply = json.choices[0].message.content.trim();
            // Strip thinking tags if present
            reply = reply.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
            if (!reply.startsWith('/')) {
                process.exit(1);
            }
            console.log(reply);
        } catch (e) {
            process.exit(1);
        }
    });
});

req.on('timeout', () => { req.destroy(); process.exit(1); });
req.on('error', () => process.exit(1));
req.write(payload);
req.end();
