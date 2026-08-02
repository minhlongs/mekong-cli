#!/usr/bin/env node
/**
 * memory-manager.cjs - Incremental Memory Management for KV Cache Optimization
 *
 * Design Principles:
 *   - Never rewrite the entire memory every request
 *   - Append, merge, or patch only changed entries
 *   - Repository context generated once, reused forever unless repo changes
 *   - Memory updates are deterministic (same input → same output)
 *   - Compaction only touches dynamic history, never static prefix
 *
 * KV Cache Optimization:
 *   - Full memory rewrites change the prompt prefix → break KV cache
 *   - Incremental appends keep the prefix stable
 *   - Only the last line(s) change, keeping the bulk of the prefix cached
 *
 * @module memory-manager
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ═════════════════════════════════════════════════════════════════════════════
// FILE PATHS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Get the memory directory path for the current project.
 *
 * @param {string} projectRoot - Project root directory
 * @param {string} [configDirName='.claude'] - Config directory name
 * @returns {string} Path to memory directory
 */
function getMemoryDir(projectRoot, configDirName = '.claude') {
  return path.join(projectRoot, configDirName, 'projects', path.basename(projectRoot), 'memory');
}

/**
 * Get the MEMORY.md index path.
 *
 * @param {string} projectRoot - Project root directory
 * @returns {string} Path to MEMORY.md
 */
function getMemoryIndexPath(projectRoot) {
  return path.join(projectRoot, 'MEMORY.md');
}

/**
 * Get the repository context cache path.
 * This stores a deterministic repo summary that never changes unless repo changes.
 *
 * @param {string} projectRoot - Project root directory
 * @returns {string} Path to repo context cache
 */
function getRepoContextPath(projectRoot) {
  const memoryDir = path.join(projectRoot, '.claude', 'cache');
  return path.join(memoryDir, 'repo-context.json');
}

// ═════════════════════════════════════════════════════════════════════════════
// DETERMINISTIC REPO CONTEXT
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Compute a deterministic repository fingerprint from git state.
 * Used to detect when repo context needs regeneration.
 *
 * @param {string} projectRoot - Project root directory
 * @returns {string|null} Fingerprint hash or null if not a git repo
 */
function computeRepoFingerprint(projectRoot) {
  try {
    const { execSync } = require('child_process');
    // Use git HEAD hash + remote URL as fingerprint
    // These are stable across sessions
    const headHash = execSync('git rev-parse HEAD', {
      cwd: projectRoot,
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    const remoteUrl = execSync('git config --get remote.origin.url', {
      cwd: projectRoot,
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();

    // Deterministic hash of repo identity
    const hash = crypto.createHash('sha256')
      .update(headHash + '|' + remoteUrl)
      .digest('hex');

    return hash;
  } catch {
    return null;
  }
}

/**
 * Check if the cached repo context is still valid (repo hasn't changed).
 *
 * @param {string} projectRoot - Project root directory
 * @returns {boolean} true if cache is valid
 */
function isRepoContextValid(projectRoot) {
  try {
    const cachePath = getRepoContextPath(projectRoot);
    if (!fs.existsSync(cachePath)) return false;

    const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
    const currentFingerprint = computeRepoFingerprint(projectRoot);

    return currentFingerprint !== null && cache.fingerprint === currentFingerprint;
  } catch {
    return false;
  }
}

/**
 * Load cached repository context (deterministic, regenerated only when repo changes).
 *
 * @param {string} projectRoot - Project root directory
 * @returns {Object|null} Cached repo context or null
 */
function loadRepoContext(projectRoot) {
  try {
    const cachePath = getRepoContextPath(projectRoot);
    if (!fs.existsSync(cachePath)) return null;

    const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
    if (!isRepoContextValid(projectRoot)) return null;

    return cache.context || null;
  } catch {
    return null;
  }
}

/**
 * Save repository context to cache.
 *
 * @param {string} projectRoot - Project root directory
 * @param {Object} context - Repository context object
 */
function saveRepoContext(projectRoot, context) {
  try {
    const cacheDir = path.dirname(getRepoContextPath(projectRoot));
    if (!fs.existsSync(cacheDir)) {
      fs.mkdirSync(cacheDir, { recursive: true });
    }

    const fingerprint = computeRepoFingerprint(projectRoot);
    if (!fingerprint) return;

    const tmpFile = getRepoContextPath(projectRoot) + '.' + Date.now() + '.tmp';
    fs.writeFileSync(tmpFile, JSON.stringify({ fingerprint, context, cachedAt: Date.now() }, null, 2));
    fs.renameSync(tmpFile, getRepoContextPath(projectRoot));
  } catch {
    // Best-effort
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// INCREMENTAL MEMORY UPDATES
// ═════════════════════════════════════════════════════════════════════════════

/**
 * List all memory files in the memory directory.
 *
 * @param {string} projectRoot - Project root directory
 * @param {string} [configDirName='.claude'] - Config directory name
 * @returns {string[]} Array of memory filenames
 */
function listMemoryFiles(projectRoot, configDirName = '.claude') {
  try {
    const memoryDir = getMemoryDir(projectRoot, configDirName);
    if (!fs.existsSync(memoryDir)) return [];

    return fs.readdirSync(memoryDir)
      .filter(f => f.endsWith('.md'))
      .sort();
  } catch {
    return [];
  }
}

/**
 * Check if a memory file with the given name already exists.
 *
 * @param {string} name - Memory name (from frontmatter, kebab-case)
 * @param {string} projectRoot - Project root directory
 * @returns {boolean} true if exists
 */
function memoryExists(name, projectRoot, configDirName = '.claude') {
  const memoryFiles = listMemoryFiles(projectRoot, configDirName);
  for (const f of memoryFiles) {
    try {
      const content = fs.readFileSync(
        path.join(getMemoryDir(projectRoot, configDirName), f),
        'utf8'
      );
      if (content.startsWith('---\n') && content.includes(`name: ${name}\n`)) {
        return true;
      }
    } catch { /* skip unreadable */ }
  }
  return false;
}

/**
 * Read a memory file by name.
 *
 * @param {string} name - Memory name (from frontmatter)
 * @param {string} projectRoot - Project root directory
 * @returns {Object|null} { filename, content, frontmatter, body } or null
 */
function readMemoryByName(name, projectRoot, configDirName = '.claude') {
  const memoryFiles = listMemoryFiles(projectRoot, configDirName);
  for (const f of memoryFiles) {
    try {
      const fullPath = path.join(getMemoryDir(projectRoot, configDirName), f);
      const content = fs.readFileSync(fullPath, 'utf8');
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
      if (frontmatterMatch) {
        const frontmatterStr = frontmatterMatch[1];
        const frontmatter = {};
        for (const line of frontmatterStr.split('\n')) {
          const sep = line.indexOf(': ');
          if (sep > 0) {
            frontmatter[line.slice(0, sep).trim()] = line.slice(sep + 2).trim();
          }
        }
        if (frontmatter.name === name) {
          return { filename: f, content, frontmatter, body: frontmatterMatch[2].trim() };
        }
      }
    } catch { /* skip */ }
  }
  return null;
}

/**
 * PATCH a memory file — only overwrite if content has changed.
 * This prevents unnecessary writes that change file timestamps and content hashes.
 *
 * @param {string} filePath - Absolute path to memory file
 * @param {string} newContent - New content to write
 * @returns {boolean} true if file was actually written (content changed)
 */
function patchMemoryFile(filePath, newContent) {
  try {
    // Read existing content
    let existing = null;
    try {
      existing = fs.readFileSync(filePath, 'utf8');
    } catch { /* file doesn't exist yet */ }

    // Only write if content has actually changed
    if (existing !== null && existing === newContent) {
      return false; // No change needed
    }

    // Atomic write
    const tmpFile = filePath + '.' + Date.now() + '.tmp';
    fs.writeFileSync(tmpFile, newContent, 'utf8');
    fs.renameSync(tmpFile, filePath);
    return true;
  } catch {
    return false;
  }
}

/**
 * APPEND a line to MEMORY.md index if it doesn't already exist.
 * Uses deterministic content — no timestamps.
 *
 * @param {string} projectRoot - Project root directory
 * @param {string} line - Index line to append (e.g., "- [Title](file.md) — hook")
 * @returns {boolean} true if line was appended
 */
function appendMemoryIndexLine(projectRoot, line) {
  try {
    const indexPath = getMemoryIndexPath(projectRoot);

    // Read existing index
    let existing = '';
    try {
      existing = fs.readFileSync(indexPath, 'utf8');
    } catch { /* file doesn't exist yet */ }

    // Check if line already exists (avoid duplicates)
    const lines = existing.split('\n').filter(l => l.trim());
    if (lines.some(l => l === line || l.startsWith(line.split(' — ')[0]))) {
      return false; // Already exists
    }

    // Append line
    const newContent = existing.trimEnd() + '\n' + line + '\n';
    fs.writeFileSync(indexPath, newContent, 'utf8');
    return true;
  } catch {
    return false;
  }
}

/**
 * ENSURE MEMORY.md index exists.
 * Creates an empty one if not found.
 *
 * @param {string} projectRoot - Project root directory
 * @returns {boolean} true if file was created
 */
function ensureMemoryIndex(projectRoot) {
  const indexPath = getMemoryIndexPath(projectRoot);
  if (fs.existsSync(indexPath)) return false;

  try {
    fs.writeFileSync(indexPath, '# Memory Index\n\n', 'utf8');
    return true;
  } catch {
    return false;
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// COMPACTION STRATEGY
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build a deterministic summary of old dynamic history for compaction.
 *
 * Compaction rules (from KV cache optimization):
 *   - NEVER compact: System Prompt, Static Context, Coding Rules
 *   - Compact only: Old conversations, old execution logs, previous reasoning, finished subtasks
 *   - The compacted summary replaces ONLY the dynamic history
 *   - Static prefix must remain untouched
 *
 * @param {Object} sessionStats - Summary of session activity
 * @returns {string} Deterministic summary
 */
function buildCompactionSummary(sessionStats = {}) {
  const lines = [
    '## Compacted History',
    '',
    `- Total tool calls: ${sessionStats.toolCalls || 'unknown'}`,
    `- Total agent spawns: ${sessionStats.agentSpawns || 'unknown'}`,
    `- Files modified: ${sessionStats.filesModified || 'unknown'}`,
    `- Current phase: ${sessionStats.currentPhase || 'unknown'}`,
    `- Completed tasks: ${sessionStats.completedTasks || 'unknown'}`,
    '',
    '## Active State',
    '',
    `- User request: ${sessionStats.currentRequest || 'unknown'}`,
    `- Last tool: ${sessionStats.lastTool || 'unknown'}`
  ];

  return lines.join('\n');
}

/**
 * Parse a transcript to extract session stats for compaction summary.
 *
 * @param {string} transcriptPath - Path to transcript JSONL file
 * @returns {Object} Session stats
 */
function extractSessionStats(transcriptPath) {
  try {
    const { parseTranscript } = require('./transcript-parser.cjs');

    // This is async but we need sync — use a simple sync version
    const content = fs.readFileSync(transcriptPath, 'utf8');
    const lines = content.split('\n').filter(l => l.trim());
    const toolCalls = lines.filter(l => l.includes('"tool_use"')).length;
    const agentSpawns = lines.filter(l => l.includes('"Task"')).length;
    const errors = lines.filter(l => l.includes('"is_error":true')).length;

    return {
      toolCalls,
      agentSpawns,
      filesModified: 0, // Not easily parseable from JSONL sync
      currentPhase: 'in-progress',
      completedTasks: 0
    };
  } catch {
    return {};
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═════════════════════════════════════════════════════════════════════════════

module.exports = {
  // File path resolution
  getMemoryDir,
  getMemoryIndexPath,
  getRepoContextPath,

  // Deterministic repo context
  computeRepoFingerprint,
  isRepoContextValid,
  loadRepoContext,
  saveRepoContext,

  // Incremental memory updates
  listMemoryFiles,
  memoryExists,
  readMemoryByName,
  patchMemoryFile,
  appendMemoryIndexLine,
  ensureMemoryIndex,

  // Compaction
  buildCompactionSummary,
  extractSessionStats
};
