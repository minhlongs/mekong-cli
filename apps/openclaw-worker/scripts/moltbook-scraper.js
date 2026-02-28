#!/usr/bin/env node
/**
 * moltbook-scraper.js — Scrape moltbook.com for trending AI agent activity
 * Called hourly by CTO's deep-loop.
 * Saves intel to knowledge/moltbook-intel/
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const MOLTBOOK_URLS = [
    'https://www.moltbook.com/',
    'https://www.moltbook.com/m',        // Submolts
    'https://www.moltbook.com/u',        // Agents
    'https://www.moltbook.com/skill.md', // Agent skill spec
];

const INTEL_DIR = path.join(__dirname, '..', 'knowledge', 'moltbook-intel');

function fetchUrl(url) {
    return new Promise((resolve, reject) => {
        const req = https.get(url, { timeout: 15000 }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ url, status: res.statusCode, body: data.slice(0, 5000) }));
        });
        req.on('error', e => resolve({ url, status: 0, error: e.message }));
        req.on('timeout', () => { req.destroy(); resolve({ url, status: 0, error: 'timeout' }); });
    });
}

async function scrape() {
    if (!fs.existsSync(INTEL_DIR)) fs.mkdirSync(INTEL_DIR, { recursive: true });

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const results = await Promise.all(MOLTBOOK_URLS.map(fetchUrl));

    const report = {
        scraped_at: new Date().toISOString(),
        results: results.map(r => ({
            url: r.url,
            status: r.status,
            error: r.error || null,
            excerpt: r.body ? r.body.slice(0, 2000) : null,
        })),
    };

    const outFile = path.join(INTEL_DIR, `moltbook-${timestamp}.json`);
    fs.writeFileSync(outFile, JSON.stringify(report, null, 2));
    console.log(`[MOLTBOOK] Scraped ${results.length} URLs → ${outFile}`);

    // Keep only last 24 files (hourly × 24h)
    const files = fs.readdirSync(INTEL_DIR).filter(f => f.startsWith('moltbook-')).sort();
    if (files.length > 24) {
        files.slice(0, files.length - 24).forEach(f => {
            try { fs.unlinkSync(path.join(INTEL_DIR, f)); } catch { }
        });
    }

    return report;
}

if (require.main === module) {
    scrape().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
}

module.exports = { scrape };
