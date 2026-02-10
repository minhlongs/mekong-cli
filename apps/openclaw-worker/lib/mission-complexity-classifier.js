/**
 * Mission Complexity Classifier — Routes missions to appropriate execution format
 *
 * SIMPLE  → /cook "task" --auto                    (single agent, fast)
 * MEDIUM  → /cook "task" --auto --parallel          (sub-agents, parallel)
 * COMPLEX → Agent Team prompt with N teammates      (full team orchestration)
 */

const config = require('../config');

/**
 * Classify mission complexity based on task metadata and keyword analysis.
 * @param {object} task - Task object from BINH_PHAP_TASKS ({id, cmd, complexity?})
 * @param {string} project - Project name for scope context
 * @returns {'simple'|'medium'|'complex'}
 */
function classifyComplexity(task, project) {
  // Explicit complexity from task config takes priority
  if (task.complexity) return task.complexity;

  // Keyword-based fallback classification
  const text = `${task.cmd} ${task.id}`.toLowerCase();

  if (config.COMPLEXITY.COMPLEX_KEYWORDS.some(kw => text.includes(kw))) return 'complex';
  if (config.COMPLEXITY.MEDIUM_KEYWORDS.some(kw => text.includes(kw))) return 'medium';
  return 'simple';
}

/**
 * Generate the mission prompt in the format appropriate for the complexity level.
 * @param {object} task - Task object ({id, cmd, complexity?})
 * @param {string} project - Target project name
 * @param {'simple'|'medium'|'complex'} complexity - Classified complexity
 * @returns {string} Formatted mission prompt for CC CLI
 */
function generateMissionPrompt(task, project, complexity) {
  const mission = `${task.cmd} in ${project}`;

  if (complexity === 'complex') {
    const teamSize = config.AGENT_TEAM_SIZE_DEFAULT;
    // Agent Team prompt — CC CLI with CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
    // will parse this and spawn a coordinated team
    return [
      `Create an agent team with ${teamSize} teammates to: ${mission}.`,
      'Assign ownership:',
      `- Teammate 1 (scout): Scan the ${project} codebase, identify all files and patterns relevant to the task`,
      `- Teammate 2 (implementer): Implement the changes identified by scout`,
      `- Teammate 3 (tester): Run tests, verify changes compile, check for regressions`,
      `- Teammate 4 (reviewer): Code review all changes, verify quality standards`,
      'Coordinate sequentially: scout first, then implementer, then tester+reviewer in parallel.',
      'Report final summary when all teammates complete.',
    ].join(' ');
  }

  if (complexity === 'medium') {
    return `/cook "${mission}" --auto --parallel`;
  }

  // simple
  return `/cook "${mission}" --auto`;
}

/**
 * Check if a mission prompt is a team mission (for timeout decisions).
 * @param {string} prompt - The full mission prompt text
 * @returns {boolean}
 */
function isTeamMission(prompt) {
  const lower = prompt.toLowerCase();
  return lower.includes('agent team') || lower.includes('teammates') || lower.includes('teammate');
}

module.exports = { classifyComplexity, generateMissionPrompt, isTeamMission };
