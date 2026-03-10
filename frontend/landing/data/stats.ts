// Real counts derived from factory/ registry files and git history.
// commands: 176 contracts in factory/contracts/commands/
// agents:   14 entries in factory/contracts/agents.registry.json
// skills:   58 entries in factory/contracts/skills.registry.json
// layers:   5 (founder / business / product / engineering / ops)
// commits:  git rev-list --count HEAD → 1906

export const STATS = {
  commands: 176,
  agents: 14,
  skills: 58,
  layers: 5,
  commits: 1906,
} as const

export type Stats = typeof STATS
