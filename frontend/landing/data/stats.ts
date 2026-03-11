// Real counts from architecture: 289 commands, 127 agents, 216 skills.
// layers: 5 (founder / business / product / engineering / ops)
// commits: approximate, updated periodically

export const STATS = {
  commands: 297,
  agents: 127,
  skills: 216,
  layers: 5,
  commits: 2000,
} as const

export type Stats = typeof STATS
