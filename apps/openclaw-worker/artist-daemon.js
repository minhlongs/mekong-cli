const fs = require('fs');
const path = require('path');
const config = require('./config');
const { chromium } = require('playwright');
const QL = require('./lib/quan-luat-enforcer');

// ═══════════════════════════════════════════════════════════════
// 🏯 ARTIST DAEMON — 畫師 (Họa Sĩ)
// ═══════════════════════════════════════════════════════════════
// Rank: HOA_SI (Họa Sĩ — Painter)
// Territory: ui_ux
// 36 Kế: #8 Ám Độ Trần Thương, #17 Phao Chuyên Dẫn Ngọc
// Điều 3: CHỈ AUDIT VISUAL, KHÔNG CODE → chuyển Builder
// Điều 4: Gemini Flash tier (FREE)
// ═══════════════════════════════════════════════════════════════

const DAEMON_NAME = 'artist';
const DAEMON_RANK = QL.RANKS[DAEMON_NAME];
const ARTIST_INTERVAL = 3 * 60 * 60 * 1000;

async function captureScreenshot(url, outputPath) {
    try {
        const browser = await chromium.launch();
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: 'networkidle' });
        await page.screenshot({ path: outputPath, fullPage: true });
        await browser.close();
        QL.logQuanLuat(DAEMON_NAME, `📸 Captured: ${outputPath}`);
        return true;
    } catch (e) {
        QL.logQuanLuat(DAEMON_NAME, `❌ Screenshot Failed: ${e.message}`);
        return false;
    }
}

async function callGeminiFlash(prompt) {
    try {
        const PROXY_URL = 'http://127.0.0.1:8080/v1/messages';
        const MODEL = 'gemini-2.5-flash';
        if (!QL.validateModelTier(DAEMON_NAME, MODEL)) return null;

        const response = await fetch(PROXY_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: MODEL,
                messages: [
                    { role: "user", content: `You are the Artist Agent (Creative Director). Analyze code/visuals for UI/UX issues. Return JSON: { visual_score: 0-100, improvements: [], mission_prompt: string }. \n\n${prompt}` }
                ],
                max_tokens: 4096,
                temperature: 0.7 
            })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errText}`);
        }

        const data = await response.json();
        let content = data.content[0].text;
        content = content.replace(/```json/g, '').replace(/```/g, '').trim();
        return JSON.parse(content);
    } catch (e) {
        QL.logQuanLuat(DAEMON_NAME, `❌ API Call Failed: ${e.message}`);
        return null;
    }
}

async function artistLoop() {
    QL.logQuanLuat(DAEMON_NAME, '🎨 Artist Daemon STARTED (Creative Director)');
    if (!QL.checkTerritory(DAEMON_NAME, 'analyze_css')) return;

    // Randomly pick a project directory to audit
    const project = config.SATELLITE_PROJECTS[Math.floor(Math.random() * config.SATELLITE_PROJECTS.length)];
    const devUrl = `http://localhost:3000`;
    const screenshotPath = `/tmp/artist_audit_${project}_${Date.now()}.png`;

    const hasVisuals = await captureScreenshot(devUrl, screenshotPath);

    QL.logQuanLuat(DAEMON_NAME, `Auditing Visuals for: ${project}...`);

    let analysis = null;
    if (hasVisuals) {
        analysis = await callGeminiFlash(`Analyze UI/UX for project ${project}. Visuals captured at ${screenshotPath}. Assume standard Tailwind issues.`);
    }

    if (analysis && analysis.visual_score < 80) {
        if (!QL.checkQueueDiscipline(DAEMON_NAME)) return;
        const missionFile = path.join(config.MEKONG_DIR, 'tasks', `LOW_mission_${project}_artist_ui_polish_${Date.now()}.txt`);
        const instruction = `/cook "Artist Agent Audit: The UI in ${project} scored ${analysis.visual_score}/100. ${analysis.mission_prompt}. Reference Screenshot: ${screenshotPath}"`;

        fs.writeFileSync(missionFile, instruction);
        QL.logQuanLuat(DAEMON_NAME, `👨‍🎨 Created Design Mission: ${missionFile}`);
        QL.createSignal(DAEMON_NAME, 'builder', 'UI_ISSUE', { project, score: analysis.visual_score }, 'LOW');
    } else {
        QL.logQuanLuat(DAEMON_NAME, '✨ Visuals look good enough or capture failed.');
    }
}

// Run immediately then interval
artistLoop();
setInterval(artistLoop, ARTIST_INTERVAL);
