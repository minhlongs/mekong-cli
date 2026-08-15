import type { D1Database } from '@cloudflare/workers-types'

export interface AgentAction {
  agent_name: string
  agent_layer: 'studio' | 'founder' | 'business' | 'product' | 'engineering' | 'ops'
  action_type: 'read' | 'write' | 'delete' | 'deploy' | 'spend' | 'communicate'
  resource: string
  tenant_id: string
  estimated_cost_usd?: number
  target_stakeholder_id?: string
}

export interface EnforcementResult {
  allowed: boolean
  layer_checked: string
  rule_violated?: string
  suggestion?: string
}

// Layer 1: FIREWALL — absolute, no override
function checkFirewall(action: AgentAction): EnforcementResult | null {
  if (action.action_type === 'spend' && (action.estimated_cost_usd || 0) > 500) {
    return {
      allowed: false,
      layer_checked: 'firewall',
      rule_violated: '1.4: Transaction >$500 needs human approval',
      suggestion: 'Queue for human review via /v1/conflicts',
    }
  }
  if (
    action.action_type === 'write' &&
    ['equity_grants', 'governance_config', 'constitution'].includes(action.resource)
  ) {
    return {
      allowed: false,
      layer_checked: 'firewall',
      rule_violated: '1.5: AI cannot modify equity/governance/constitution',
      suggestion: 'Submit proposal via /v1/governance/proposals',
    }
  }
  if (
    action.action_type === 'delete' &&
    ['stakeholders', 'ledger_accounts', 'equity_entities'].includes(action.resource)
  ) {
    return {
      allowed: false,
      layer_checked: 'firewall',
      rule_violated: '1.2: Cannot delete core governance data',
      suggestion: 'Use soft-delete status field instead',
    }
  }
  return null
}

// Layer 2: STAKEHOLDER BALANCE — 75% supermajority to amend
function checkBalance(action: AgentAction): EnforcementResult | null {
  if (
    action.agent_layer === 'business' &&
    action.action_type === 'communicate' &&
    !action.target_stakeholder_id
  ) {
    return {
      allowed: false,
      layer_checked: 'balance',
      rule_violated: '2.1: External communication needs target stakeholder',
      suggestion: 'Specify target_stakeholder_id',
    }
  }
  return null
}

// Layer 3: AGENT RULES — per-layer autonomy
const LAYER_AUTONOMY: Record<string, string[]> = {
  studio: ['read', 'write', 'communicate'],
  founder: ['read', 'write', 'communicate'],
  business: ['read', 'write'],
  product: ['read', 'write'],
  engineering: ['read', 'write', 'deploy'],
  ops: ['read', 'write', 'communicate'],
}

function checkAgentRules(action: AgentAction): EnforcementResult | null {
  const allowed = LAYER_AUTONOMY[action.agent_layer] || ['read']
  if (!allowed.includes(action.action_type)) {
    return {
      allowed: false,
      layer_checked: 'agent_rules',
      rule_violated: `Layer ${action.agent_layer} cannot ${action.action_type}`,
      suggestion: `Escalate to layer with ${action.action_type} permission`,
    }
  }
  return null
}

// Layer 4: TERRAIN — Cửu Địa adaptive from Ngũ Sự scores
async function checkTerrain(action: AgentAction, db: D1Database): Promise<EnforcementResult | null> {
  const score = await db
    .prepare('SELECT terrain, overall_score FROM ngu_su_scores WHERE tenant_id = ? ORDER BY scored_at DESC LIMIT 1')
    .bind(action.tenant_id)
    .first<{ terrain: string; overall_score: number }>()
  if (!score) return null
  if (score.terrain === 'tu_dia' && action.action_type === 'spend') {
    return {
      allowed: false,
      layer_checked: 'terrain',
      rule_violated: 'Tử Địa: all spending frozen',
      suggestion: 'Survival mode — escalate to human',
    }
  }
  return null
}

export async function enforceConstitution(action: AgentAction, db?: D1Database): Promise<EnforcementResult> {
  const firewall = checkFirewall(action)
  if (firewall) return firewall

  const balance = checkBalance(action)
  if (balance) return balance

  const agentRule = checkAgentRules(action)
  if (agentRule) return agentRule

  if (db) {
    const terrain = await checkTerrain(action, db)
    if (terrain) return terrain
  }

  return { allowed: true, layer_checked: 'all_passed' }
}
