#!/usr/bin/env node
/**
 * ZuneF JWT expiry hook — FORCE Workflow for ALL tasks.
 *
 * ZuneF JWT expires in 15 minutes. Every task MUST be executed via
 * Workflow tool -> subagents. Each subagent gets a fresh JWT.
 * Main session is STRICTLY a coordinator.
 */
'use strict';
try {
  var stdin = require('fs').readFileSync(0, 'utf-8').trim();
  if (!stdin) { console.log(JSON.stringify({ continue: true })); process.exit(0); }

  var payload = JSON.parse(stdin);
  if ((payload.hook_event_name || '') !== 'UserPromptSubmit') {
    console.log(JSON.stringify({ continue: true })); process.exit(0);
  }

  var prompt = String(payload.prompt || payload.user_prompt || '').trim();
  if (!prompt) { console.log(JSON.stringify({ continue: true })); process.exit(0); }

  var ctx = '';
  ctx += '\n';
  ctx += '## ZuneF Execution Mode: MANDATORY Workflow\n';
  ctx += '\n';
  ctx += '**CRITICAL RULE — Do NOT skip. Applies to EVERY user request.**\n';
  ctx += '\n';
  ctx += 'ZuneF JWTs expire in exactly **15 minutes**. NEVER execute work directly.\n';
  ctx += '\n';
  ctx += '### Available models (pure Opus tier):\n';
  ctx += '- `claude-opus-4-8` - Default (Opus tier)\n';
  ctx += '- `claude-opus-4-7` - Middle tier (Sonnet slot)\n';
  ctx += '- `claude-opus-4-6` - Fastest (Haiku slot)\n';
  ctx += '- NO China models (NIM NVIDIA free tier - remove, unstable)\n';
  ctx += '\n';
  ctx += '### Execution: Workflow only, Opus-only models\n';
  ctx += '1. ALL tasks -> Workflow -> subagents -> fresh JWT\n';
  ctx += '2. Subagents use Opus 4.8/4.7/4.6 per CK init 3-tier\n';
  ctx += '3. Main session = coordination ONLY\n';
  ctx += '4. No China models, no hybrid routing\n';
  ctx += '\n';
  ctx += '### DO NOT:\n';
  ctx += '- Handle tasks directly in main session\n';
  ctx += '- Think "this is too small for Workflow"\n';
  ctx += '- Execute code, read files, or call APIs in main session\n';
  ctx += '\n';
  ctx += '### DO:\n';
  ctx += '- Spawn Workflow for EVERY user request\n';
  ctx += '- Keep main session thin - just route and compile\n';
  ctx += '- Use `claude --print` for subagents (fast, no overhead)\n';
  ctx += '\n';

  var output = {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: ctx
    }
  };

  console.log(JSON.stringify(output));
} catch (e) {
  // fail-open: don't break the session
}
process.exit(0);
