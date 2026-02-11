/**
 * Quota Tracker — Token consumption monitoring per mission/project/channel
 *
 * Reads proxy's usage-history.json to calculate real consumption.
 * Tracks per-mission token estimates via request/response size.
 * Provides interface for future channel separation (dev-brain vs marketing).
 *
 * Usage:
 *   const qt = require('./quota-tracker');
 *   qt.recordMission({ project: 'sophia', prompt, elapsed, paneIdx });
 *   qt.getSummary();  // { today, hour, byProject, byChannel }
 */

const fs = require('fs');
const path = require('path');
const config = require('../config');

const USAGE_HISTORY = path.join(
  process.env.HOME || '',
  '.config/antigravity-proxy/usage-history.json'
);

const TRACKER_FILE = path.join(
  config.OPENCLAW_HOME || path.join(process.env.HOME || '', '.openclaw'),
  'quota-tracking.json'
);

// Rough token estimation: ~4 chars per token (English/Vietnamese mix)
const CHARS_PER_TOKEN = 4;

// Channel definitions for quota separation
const CHANNELS = {
  DEV_BRAIN: 'dev-brain',       // Tôm Hùm missions
  MARKETING: 'marketing',       // Future: Marketing Agent
  INTERACTIVE: 'interactive',   // Manual CC CLI sessions
};

let trackingData = { missions: [], dailyTotals: {} };

function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function loadTracking() {
  try {
    if (fs.existsSync(TRACKER_FILE)) {
      trackingData = JSON.parse(fs.readFileSync(TRACKER_FILE, 'utf-8'));
    }
  } catch (e) { /* start fresh */ }
}

function saveTracking() {
  try {
    ensureDir(TRACKER_FILE);
    // Keep only last 7 days of missions to prevent file bloat
    const cutoff = Date.now() - 7 * 24 * 3600 * 1000;
    trackingData.missions = trackingData.missions.filter(m => m.ts > cutoff);
    fs.writeFileSync(TRACKER_FILE, JSON.stringify(trackingData, null, 2));
  } catch (e) { /* non-critical */ }
}

/**
 * Record a completed mission's estimated token usage.
 * @param {object} opts
 * @param {string} opts.project - Project name (e.g. 'sophia', '84tea')
 * @param {string} opts.prompt - Full prompt text sent
 * @param {number} opts.elapsed - Mission duration in seconds
 * @param {number} [opts.paneIdx] - Tmux pane index
 * @param {string} [opts.channel] - Channel: 'dev-brain' | 'marketing'
 */
function recordMission({ project, prompt, elapsed, paneIdx, channel }) {
  const promptTokens = Math.ceil((prompt || '').length / CHARS_PER_TOKEN);
  // Response estimate: ~2x prompt for typical code generation tasks
  const responseTokens = Math.ceil(promptTokens * 2);
  const totalTokens = promptTokens + responseTokens;

  const entry = {
    ts: Date.now(),
    project: project || 'unknown',
    channel: channel || CHANNELS.DEV_BRAIN,
    promptTokens,
    responseTokens,
    totalTokens,
    elapsed: elapsed || 0,
    paneIdx: paneIdx ?? -1,
  };

  trackingData.missions.push(entry);

  // Update daily totals
  const day = new Date().toISOString().slice(0, 10);
  if (!trackingData.dailyTotals[day]) {
    trackingData.dailyTotals[day] = { total: 0, byProject: {}, byChannel: {} };
  }
  const dt = trackingData.dailyTotals[day];
  dt.total += totalTokens;
  dt.byProject[entry.project] = (dt.byProject[entry.project] || 0) + totalTokens;
  dt.byChannel[entry.channel] = (dt.byChannel[entry.channel] || 0) + totalTokens;

  saveTracking();
  return entry;
}

/**
 * Read proxy's usage-history.json for real request counts.
 * @returns {{ totalRequests: number, todayRequests: number, byModel: object }}
 */
function readProxyUsage() {
  try {
    if (!fs.existsSync(USAGE_HISTORY)) return null;
    const data = JSON.parse(fs.readFileSync(USAGE_HISTORY, 'utf-8'));
    const today = new Date().toISOString().slice(0, 10);
    let totalRequests = 0;
    let todayRequests = 0;
    const byModel = {};

    for (const [hour, val] of Object.entries(data)) {
      const count = val._total || 0;
      totalRequests += count;
      if (hour.startsWith(today)) todayRequests += count;
      for (const provider of ['claude', 'gemini']) {
        if (!val[provider]) continue;
        for (const [model, n] of Object.entries(val[provider])) {
          if (model.startsWith('_')) continue;
          const key = `${provider}/${model}`;
          byModel[key] = (byModel[key] || 0) + n;
        }
      }
    }
    return { totalRequests, todayRequests, byModel };
  } catch (e) { return null; }
}

/**
 * Get comprehensive quota summary.
 * @returns {object} Summary with today/hour stats, by project and channel
 */
function getSummary() {
  loadTracking();
  const now = Date.now();
  const hourAgo = now - 3600 * 1000;
  const today = new Date().toISOString().slice(0, 10);

  const hourMissions = trackingData.missions.filter(m => m.ts > hourAgo);
  const todayTotals = trackingData.dailyTotals[today] || { total: 0, byProject: {}, byChannel: {} };

  return {
    lastHour: {
      missions: hourMissions.length,
      estimatedTokens: hourMissions.reduce((s, m) => s + m.totalTokens, 0),
    },
    today: todayTotals,
    proxyUsage: readProxyUsage(),
    channels: CHANNELS,
  };
}

/**
 * Get quota allocation interface for a specific channel.
 * Future: enforce per-channel limits.
 * @param {string} channel
 * @returns {{ used: number, limit: number|null, remaining: number|null }}
 */
function getChannelQuota(channel) {
  loadTracking();
  const today = new Date().toISOString().slice(0, 10);
  const dt = trackingData.dailyTotals[today] || { byChannel: {} };
  const used = dt.byChannel[channel] || 0;

  // Future: configurable per-channel daily limits
  // For now, no hard limits — just tracking
  return { channel, used, limit: null, remaining: null };
}

// Initialize on require
loadTracking();

module.exports = {
  recordMission,
  getSummary,
  getChannelQuota,
  readProxyUsage,
  CHANNELS,
};
