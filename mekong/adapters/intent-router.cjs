#!/usr/bin/env node
/**
 * Intent Router — Classifies user requests by complexity + domain + mode,
 * then routes to the correct model + agent + pipeline.
 *
 * Usage:
 *   node intent-router.cjs "Fix login redirect bug on Safari"
 *   echo "Add user auth" | node intent-router.cjs
 *   node intent-router.cjs "Deploy to production" --priority critical
 *   node intent-router.cjs --file /path/to/input.txt
 *
 * Output: JSON classification to stdout.
 * Error: JSON with { error: "..." } to stderr, exit code 1.
 */
"use strict";

// ──────────────────────────────────────────────
// 1. Lexicon — action verbs, domain nouns, modifiers
// ──────────────────────────────────────────────

const LEXICON = {
  actions: {
    cook: [
      "build", "create", "add", "implement", "make", "generate",
      "write", "produce", "setup", "configure", "integrate",
      "migrate", "refactor", "extract", "convert", "transform",
    ],
    plan: [
      "design", "architect", "plan", "draft", "outline",
      "spec", "blueprint", "whiteboard",
    ],
    fix: [
      "fix", "debug", "resolve", "repair", "patch", "hotfix",
      "correct", "remediate", "recover", "undo",
    ],
    test: [
      "test", "validate", "verify", "assert", "check",
      "qa", "regression", "lint",
    ],
    deploy: [
      "deploy", "ship", "release", "publish", "launch",
      "rollout", "promote", "cut release",
    ],
    review: [
      "review", "audit", "analyze", "inspect", "scan",
      "assess", "evaluate", "examine", "profile",
    ],
  },

  domains: {
    engineering: [
      "api", "database", "db", "sql", "nosql", "build", "deploy",
      "test", "infra", "infrastructure", "docker", "ci", "cd",
      "pipeline", "code", "backend", "frontend", "server", "client",
      "middleware", "endpoint", "route", "schema", "migration",
      "config", "configuration", "typescript", "javascript", "node",
      "npm", "package", "module", "dependency", "sdk", "library",
      "framework", "compiler", "bundler", "webpack", "vite",
      "monorepo", "turborepo", "nx", "graphql", "rest", "grpc",
      "websocket", "cache", "redis", "queue", "worker", "cron",
      "logging", "monitoring", "otel", "telemetry", "performance",
      "optimize", "optimization", "refactor", "techdebt",
    ],
    business: [
      "revenue", "billing", "invoice", "payment", "subscription",
      "pricing", "tier", "plan", "marketing", "sales", "finance",
      "customer", "client", "account", "contract", "license",
      "saas", "mrr", "arr", "churn", "lifetime", "ltv",
      "cac", "roi", "profit", "cost", "budget", "forecast",
      "analytics", "dashboard", "report", "kpi", "metric",
      "campaign", "email", "newsletter", "lead", "conversion",
      "funnel", "retention", "engagement", "onboarding",
      "trial", "freemium", "upsell", "cross-sell", "partner",
    ],
    product: [
      "feature", "ux", "user experience", "ui", "design",
      "user", "roadmap", "research", "usability", "accessibility",
      "a11y", "i18n", "localization", "prototype", "mockup",
      "wireframe", "figma", "component", "pattern", "style",
      "theme", "color", "typography", "layout", "responsive",
      "mobile", "desktop", "landing", "page", "screen",
      "navigation", "sidebar", "modal", "form", "button",
      "interaction", "animation", "motion", "feedback", "notification",
      "empty state", "loading", "skeleton", "error state",
      "persona", "journey", "story", "epic", "priority",
    ],
    ops: [
      "security", "auth", "authentication", "authorization",
      "oauth", "sso", "rbac", "permission", "role", "audit",
      "compliance", "gdpr", "hipaa", "soc2", "pci", "legal",
      "hr", "people", "onboard", "offboard", "employee",
      "monitor", "monitoring", "alert", "incident", "pager",
      "sla", "uptime", "reliability", "backup", "disaster",
      "recovery", "dr", "failover", "redundancy", "scaling",
      "autoscale", "load", "stress", "chaos", "penetration",
      "vulnerability", "cve", "patch", "update", "upgrade",
    ],
  },

  complexity: {
    fast: [
      "quick", "fast", "simple", "typo", "minor", "tiny",
      "small change", "rename", "delete", "remove",
    ],
    critical: [
      "production", "prodcution", "prodfix", "critical",
      "urgent", "crash", "data loss", "outage", "p0",
      "p1", "security", "vulnerability", "breach", "down",
      "blocking", "blocker", "emergency", "hotfix",
    ],
  },

  // special patterns for complex detection
  complexPatterns: [
    /integrat(e|ion).*\w{3,}\s+(api|service|provider|system)/i,
    /architect(ure)?\s+(of|for|with)/i,
    /migrat(e|ion).*(from|to).*(legacy|new|cloud|server)/i,
    /new\s+(feature|module|service|system|platform)/i,
    /multi(\s|-)?(file|module|service|tenant|region)/i,
    /microservice/i,
    /event.?driven/i,
    /distributed\s+system/i,
    /build\s+(\w+\s+)?(auth|authentication|authorization|system|service|module|platform|pipeline)s?\b/i,
    /implement\s+(\w+\s+)?(auth|authentication|authorization|system|service|module|platform)s?\b/i,
    /create\s+(\w+\s+)?(auth|authentication|authorization|system|service|module|platform)s?\b/i,
    /add\s+(\w+\s+)?(auth|authentication|authorization|feature|module|system)s?\b/i,
  ],
};

// ──────────────────────────────────────────────
// 2. Agent + Skills mapping (domain × mode)
// ──────────────────────────────────────────────

const AGENT_MAP = {
  "engineering:cook":    { agent: "build",  skills: ["ck:cook"] },
  "engineering:plan":    { agent: "build",  skills: ["ck:plan"] },
  "engineering:fix":     { agent: "debug",  skills: ["ck:fix"] },
  "engineering:test":    { agent: "test",   skills: ["ck:test"] },
  "engineering:deploy":  { agent: "build",  skills: ["ck:devops"] },
  "engineering:review":  { agent: "review", skills: ["ck:code-review"] },
  "business:cook":       { agent: "build",  skills: ["cook", "copywriting"] },
  "business:plan":       { agent: "research", skills: ["planning"] },
  "business:fix":        { agent: "build",   skills: ["cook", "copywriting"] },
  "business:test":       { agent: "test",     skills: ["ck:test"] },
  "business:deploy":     { agent: "build",    skills: ["devops"] },
  "business:review":     { agent: "review",   skills: ["ck:code-review", "copywriting"] },
  "product:cook":        { agent: "build",    skills: ["ck:cook", "ck:frontend-design"] },
  "product:plan":        { agent: "research", skills: ["planning"] },
  "product:fix":         { agent: "debug",    skills: ["ck:fix", "ck:frontend-design"] },
  "product:test":        { agent: "test",     skills: ["ck:test"] },
  "product:deploy":      { agent: "build",    skills: ["ck:devops"] },
  "product:review":      { agent: "review",   skills: ["ck:code-review", "ck:frontend-design"] },
  "ops:cook":            { agent: "build",    skills: ["ck:cook", "ck:devops"] },
  "ops:plan":            { agent: "build",    skills: ["ck:plan"] },
  "ops:fix":             { agent: "debug",    skills: ["ck:fix", "ck:devops"] },
  "ops:test":            { agent: "test",     skills: ["ck:test", "ck:devops"] },
  "ops:deploy":          { agent: "ops",      skills: ["ck:devops"] },
  "ops:review":          { agent: "review",   skills: ["ck:code-review", "ck:devops"] },
};

const PIPELINE_MAP = {
  cook:   ["scout", "plan", "implement", "test", "review", "finalize"],
  plan:   ["research", "plan", "review"],
  fix:    ["debug", "fix", "test", "review"],
  test:   ["test"],
  deploy: ["build", "test", "commit", "push", "verify"],
  review: ["scan", "analyze", "report", "recommend"],
};

const COMPLEXITY_WEIGHTS = {
  fast:     0.3,
  standard: 0.5,
  complex:  0.7,
  critical: 0.9,
};

// ──────────────────────────────────────────────
// 3. Utilities
// ──────────────────────────────────────────────

/** Lowercase, trim, collapse whitespace */
function normalize(str) {
  return String(str).toLowerCase().replace(/\s+/g, " ").trim();
}

/** Count how many distinct lexicon items appear in the input */
function countMatches(input, wordList) {
  const lower = ` ${input} `;
  let count = 0;
  for (const word of wordList) {
    // Match whole word or compound (e.g. "data loss")
    const pattern = new RegExp(`\\b${escapeRegex(word)}\\b`, "i");
    if (pattern.test(lower)) count++;
  }
  return count;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Detect multi-file mentions (paths/globs like src/*.ts) */
function hasMultiFileRef(input) {
  return /\b(src|lib|app|packages?|modules?)\//.test(input);
}

/** Estimate file/scope size from the input */
function estimateScope(input) {
  // Count potential file/component references
  const refs = (input.match(/\b\w+\.(ts|js|tsx|jsx|py|go|rb|rs|vue|svelte)\b/g) || []);
  const mentions = (input.match(/\b(src|lib|app|packages?|modules?)\//g) || []);
  return refs.length + mentions.length;
}

// ──────────────────────────────────────────────
// 4. Classification logic
// ──────────────────────────────────────────────

function classify(input) {
  const raw = String(input).trim();
  if (!raw) {
    return { error: "Empty input — provide a user request to classify." };
  }

  const norm = normalize(raw);
  const inputLen = norm.length;

  // ── 4a. Detect mode from action verbs ───────────
  let mode = null;
  let modeConfidence = 0;
  let matchedActions = [];

  for (const [candidateMode, verbs] of Object.entries(LEXICON.actions)) {
    const found = verbs.filter((v) => {
      const re = new RegExp(`\\b${escapeRegex(v)}\\b`, "i");
      return re.test(norm);
    });
    if (found.length > 0) {
      matchedActions.push({ mode: candidateMode, verbs: found });
    }
  }

  if (matchedActions.length > 0) {
    // Pick the mode with the most matched verbs
    matchedActions.sort((a, b) => b.verbs.length - a.verbs.length);
    mode = matchedActions[0].mode;
    modeConfidence = Math.min(matchedActions[0].verbs.length / 3, 1.0);
  }

  // ── 4b. Detect domain ───────────────────────────
  let domain = null;
  let domainConfidence = 0;
  let domainMatches = {};

  for (const [candidateDomain, words] of Object.entries(LEXICON.domains)) {
    const count = countMatches(norm, words);
    if (count > 0) {
      domainMatches[candidateDomain] = count;
    }
  }

  const domainEntries = Object.entries(domainMatches);
  if (domainEntries.length > 0) {
    domainEntries.sort((a, b) => b[1] - a[1]);
    domain = domainEntries[0][0];
    domainConfidence = Math.min(domainEntries[0][1] / 4, 1.0);
  }

  // Fallback: if no domain detected, infer from mode
  if (!domain) {
    domain = "engineering"; // default for code-heavy queries
    domainConfidence = 0.3;
  }

  // ── 4c. Detect complexity ───────────────────────
  const fastCount = countMatches(norm, LEXICON.complexity.fast);
  const criticalCount = countMatches(norm, LEXICON.complexity.critical);
  const hasComplexPattern = LEXICON.complexPatterns.some((re) => re.test(norm));
  const scopeEstimate = estimateScope(norm);

  let complexity = "standard";
  let complexityRaw = 0;

  if (criticalCount > 0) {
    complexity = "critical";
    complexityRaw = 0.9;
  } else if (hasComplexPattern || scopeEstimate >= 5) {
    complexity = "complex";
    complexityRaw = 0.7;
  } else if ((fastCount > 0 && inputLen < 80) || inputLen < 20) {
    complexity = "fast";
    complexityRaw = 0.3;
  } else if (mode === "plan" || mode === "deploy") {
    complexity = "complex";
    complexityRaw = 0.7;
  } else {
    complexity = "standard";
    complexityRaw = 0.5;
  }

  // ── 4d. Resolve agent + skills ──────────────────
  const agentKey = `${domain}:${mode || "cook"}`;
  let agentConfig = AGENT_MAP[agentKey];

  // Fallback: try engineering mode
  if (!agentConfig) {
    const fallbackKey = `engineering:${mode || "cook"}`;
    agentConfig = AGENT_MAP[fallbackKey] || AGENT_MAP["engineering:cook"];
  }

  const agent = agentConfig.agent;
  const skills = [...agentConfig.skills];

  // ── 4e. Build pipeline ───────────────────────────
  let pipeline = PIPELINE_MAP[mode || "cook"] || PIPELINE_MAP.cook;
  pipeline = [...pipeline];

  // Pipeline extensions for complexity
  if (complexity === "critical") {
    pipeline.unshift("escalate");
    pipeline.push("human_review");
  } else if (complexity === "complex") {
    pipeline.push("human_review");
  }

  // ── 4f. Confidence scoring ───────────────────────
  const totalPossibleMatches = 4; // action + domain + complexity + mode
  let matched = 0;

  if (modeConfidence > 0) matched++;
  if (domainConfidence > 0) matched++;
  if (complexityRaw > 0) matched++;
  if (mode) matched++; // mode resolved

  let confidence = matched / totalPossibleMatches;

  // Blend in actual keyword match ratio for finer granularity
  const allKeywords = [
    ...Object.values(LEXICON.actions).flat(),
    ...Object.values(LEXICON.domains).flat(),
    ...Object.values(LEXICON.complexity).flat(),
  ];
  const keywordMatchRatio = countMatches(norm, allKeywords) / Math.max(allKeywords.length, 1);
  confidence = confidence * 0.6 + keywordMatchRatio * 15 * 0.4; // scale keyword ratio
  confidence = Math.min(Math.max(Math.round(confidence * 100) / 100, 0.1), 0.99);

  // ── 4g. Assemble result ─────────────────────────
  const result = {
    source: "user",
    intent: raw,
    domain,
    complexity,
    mode: mode || "cook",
    agent,
    skills,
    pipeline,
    confidence,
  };

  if (confidence < 0.5) {
    result.unclear = true;
    result.clarification =
      "Your request was unclear. Please provide a more specific description including an action verb (e.g. build, fix, test) and a domain (e.g. API, database, UI, auth).";
  }

  return result;
}

// ──────────────────────────────────────────────
// 5. CLI / stdin input parsing
// ──────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2); // skip node + script
  const result = { input: null, priority: null, file: null };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--priority" || arg === "-p") {
      result.priority = args[++i] || null;
    } else if (arg === "--file" || arg === "-f") {
      result.file = args[++i] || null;
    } else if (arg === "--help" || arg === "-h") {
      showHelp();
      process.exit(0);
    } else if (arg.startsWith("--")) {
      // skip unknown flags
    } else {
      // positional input
      result.input = arg;
    }
  }

  return result;
}

function showHelp() {
  console.log(`
Intent Router — Classify a user request and route to the correct pipeline.

Usage:
  node intent-router.cjs <request>
  echo "<request>" | node intent-router.cjs
  node intent-router.cjs --file <path>
  node intent-router.cjs <request> --priority <complexity>

Options:
  --priority, -p   Override complexity: fast, standard, complex, critical
  --file, -f       Read input from file
  --help, -h       Show this help

Examples:
  node intent-router.cjs "Fix login redirect on Safari"
  node intent-router.cjs "Build user auth with OAuth2" --priority critical
  echo "Deploy to production" | node intent-router.cjs
`);
}

function readFileSync(filepath) {
  const fs = require("fs");
  return fs.readFileSync(filepath, "utf-8").trim();
}

// ──────────────────────────────────────────────
// 6. Main
// ──────────────────────────────────────────────

function main() {
  let result;

  try {
    const parsed = parseArgs(process.argv);
    let input = parsed.input;

    // Priority override
    if (parsed.priority) {
      const validPriorities = ["fast", "standard", "complex", "critical"];
      if (!validPriorities.includes(parsed.priority.toLowerCase())) {
        console.error(JSON.stringify({
          error: `Invalid priority "${parsed.priority}". Must be one of: ${validPriorities.join(", ")}`,
        }));
        process.exit(1);
      }
    }

    // Read from file
    if (parsed.file) {
      input = readFileSync(parsed.file);
    }

    // Read from stdin if no input from argv
    if (!input && !process.stdin.isTTY) {
      const fs = require("fs");
      const stdinBuffer = fs.readFileSync(process.stdin.fd, "utf-8");
      input = stdinBuffer.trim();
    }

    if (!input) {
      console.error(JSON.stringify({
        error: "No input provided. Pass a string argument, pipe from stdin, or use --file.",
      }));
      process.exit(1);
    }

    result = classify(input);

    // Apply priority override
    if (parsed.priority) {
      result.complexity = parsed.priority.toLowerCase();
      // Update pipeline extensions if complexity changed
      const hasEscalate = result.pipeline[0] === "escalate";
      const hasHumanReview = result.pipeline[result.pipeline.length - 1] === "human_review";

      if (parsed.priority === "critical") {
        if (!hasEscalate) result.pipeline.unshift("escalate");
        if (!hasHumanReview) result.pipeline.push("human_review");
      } else if (parsed.priority === "complex") {
        if (hasEscalate) result.pipeline.shift();
        if (!hasHumanReview) result.pipeline.push("human_review");
      } else {
        if (hasEscalate) result.pipeline.shift();
        if (hasHumanReview) result.pipeline.pop();
      }
    }

    // Ensure pipeline is unique (no dupes from extensions)
    result.pipeline = [...new Set(result.pipeline)];

    console.log(JSON.stringify(result, null, 2));

  } catch (err) {
    console.error(JSON.stringify({
      error: err.message,
      stack: err.stack,
    }));
    process.exit(1);
  }
}

// Allow require() usage as a module
if (require.main === module) {
  main();
} else {
  module.exports = { classify, LEXICON, AGENT_MAP, PIPELINE_MAP };
}
