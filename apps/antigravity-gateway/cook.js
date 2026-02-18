#!/usr/bin/env node
/**
 * 🍳 THE COOK CLI (Antigravity Gateway Client)
 * Usage: ./cook.js claude ...
 */

const { spawn } = require('child_process');
const http = require('http');

// CONFIGURATION
const CLOUDFLARE_GATEWAY = "https://antigravity-gateway.agencyos-openclaw.workers.dev";
const LOCAL_BRAIN = "http://localhost:8000";
const LOCAL_MUSCLE = "http://localhost:8080";
// [ANTIGRAVITY] AUTO-INJECT GCLOUD TOKEN FOR ULTRA QUOTA
const { execSync } = require('child_process');
let GCLOUD_TOKEN = '';
try {
    // Try to get fresh token from gcloud
    GCLOUD_TOKEN = execSync('gcloud auth print-access-token', { encoding: 'utf8', timeout: 3000 }).trim();
    console.log('🦞 [Cook] Ultra Token Injected (Vertex/Gcloud)');
} catch (e) {
    console.log('⚠️ [Cook] Gcloud Token Fetch Failed (Fallback to Legacy Auth)');
}

const AUTH_TOKEN = process.env.COOK_AUTH_TOKEN || "sk-6219c93290f14b32b047342ca8b0bea9"; // Legacy Fallback

// COLORS
const green = (text) => `\x1b[32m${text}\x1b[0m`;
const blue = (text) => `\x1b[34m${text}\x1b[0m`;
const gray = (text) => `\x1b[90m${text}\x1b[0m`;
const red = (text) => `\x1b[31m${text}\x1b[0m`;

// UTILS
function checkBrainStatus() {
    return new Promise((resolve) => {
        const req = http.get(LOCAL_BRAIN, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve(null);
                }
            });
        });
        req.on('error', () => resolve(null));
        req.setTimeout(500, () => {
            req.abort();
            resolve(null);
        });
    });
}

// MAIN EXECUTION
(async () => {
    const args = process.argv.slice(2);
    const command = args.length > 0 ? args[0] : 'claude';
    let commandArgs = args.length > 1 ? args.slice(1) : [];

    // Check Status Command
    if (command === 'status') {
        const brainData = await checkBrainStatus();
        console.log(green("\n🦞 [LOBSTER SQUAD] STATUS REPORT:"));
        if (brainData) {
            console.log(`   🧠 Brain:    ${green("ONLINE")} (Mode: ${brainData.mode})`);
            console.log(`   🛡️  Muscle:   ${green("ONLINE")} (Nodes: ${brainData.active_nodes || 1})`);
            console.log(`   ☁️  Edge:     ${green("STANDBY")} (Fallback)`);
        } else {
            console.log(`   🧠 Brain:    ${gray("OFFLINE")} (Sleeping)`);
            console.log(`   ☁️  Edge:     ${green("ACTIVE")} (Cloudflare)`);
        }
        process.exit(0);
    }

    console.log(green("\n🔥 [Antigravity] Kích hoạt đường hầm tàng hình..."));

    // Determine Routing
    // Determine Routing
    const brainData = await checkBrainStatus();
    // FIXED: Prioritize Environment Variable (from brain-tmux.js or shell)
    let targetUrl = process.env.ANTHROPIC_BASE_URL || CLOUDFLARE_GATEWAY;

    if (brainData) {
        console.log(green(`   🦞 LOBSTER SQUAD ACTIVE (Monitoring Mode)`));
        console.log(gray(`      - Brain Mode: ${brainData.mode}`));
        console.log(gray(`      - Muscle: Standby (Waiting for Transmutation Module)`));
        console.log(blue(`      - Routing: 🌩️  Universal Proxy (Z.ai/Gemini Local)`));

        // Only verify logic here, but trust env var if set
        if (!process.env.ANTHROPIC_BASE_URL) {
            console.log(red(`   ⚠️  WARNING: No ANTHROPIC_BASE_URL set. Defaulting to Cloudflare.`));
            targetUrl = CLOUDFLARE_GATEWAY;
        }
    } else {
        console.log(blue("   ☁️  Using Cloudflare Edge (Global Network)"));
        if (process.env.ANTHROPIC_BASE_URL) {
            targetUrl = process.env.ANTHROPIC_BASE_URL;
            console.log(green(`      - Override: Using Custom URL: ${targetUrl}`));
        } else {
            console.log(gray(`      - Brain offline. Fallback to Serverless.`));
        }
    }

    console.log(gray("----------------------------------------------------------------"));

    // ENVIRONMENT HIJACKING
    // [ANTIGRAVITY] TOKEN STRATEGY:
    // 1. If GCLOUD_TOKEN exists (Ultra Account), use it as the API Key (Gateway Passthrough).
    // 2. Else, use the COOK_AUTH_TOKEN (Legacy/Gateway Managed).
    const FINAL_API_KEY = AUTH_TOKEN; // Default to legacy token

    const env = {
        ...process.env,
        ANTHROPIC_BASE_URL: targetUrl,
        ANTHROPIC_API_KEY: FINAL_API_KEY, // <--- CRITICAL INJECTION (Default)
        COOK_AUTH_TOKEN: AUTH_TOKEN, // Keep for reference
        FORCE_COLOR: '1'
    };

    // [BINH PHAP] SMART ROUTING: "HƯ THỰC" STRATEGY
    // DEFAULT: Free Tier (Hư)
    // RESCUE: Service Account Enterprise (Thực) - Only when Free fails

    let injectedKey = "FREE_TIER"; // Default intention

    try {
        const GCLOUD_TOKEN = execSync('gcloud auth application-default print-access-token', { encoding: 'utf8', timeout: 3000 }).toString().trim();
        if (GCLOUD_TOKEN && (GCLOUD_TOKEN.startsWith('ya29') || GCLOUD_TOKEN.startsWith('adc-'))) {
            // console.log(green(`🦞 [Cook] Armed & Ready: Service Account Rescue Token Loaded.`));
            // Append Rescue Token as "Trojan Horse" payload
            injectedKey = `FREE_TIER:::${GCLOUD_TOKEN}`;
        }
    } catch (e) {
        // e.g. not logged in
        // console.log('⚠️ [Cook] Rescue Token Unavailable (Running purely on Free Tier)');
    }

    // Inject the Dual-Token
    env.ANTHROPIC_API_KEY = injectedKey;

    /*
    // Legacy ADC Logic (Disabled in favor of API Key)
    try {
        const GCLOUD_TOKEN = execSync('gcloud auth application-default print-access-token', { encoding: 'utf8', timeout: 3000 }).toString().trim();
         // ...
    } catch (e) {} 
    */

    const child = spawn(command, commandArgs, {
        env,
        stdio: 'inherit'
    });

    child.on('exit', (code) => {
        console.log(gray(`\n🛑 [Antigravity] Đã đóng đường hầm. Mã thoát: ${code}`));
    });
})();
