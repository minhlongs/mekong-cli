export interface SearchResult {
  id: string
  title: string
  subtitle: string
  category: 'hub' | 'action' | 'recent' | 'setting'
  icon: string
  path?: string
  action?: () => void
  keywords: string[]
}

export const SEARCH_INDEX: SearchResult[] = [
  { id: 'war-room', title: 'War Room', subtitle: 'Mission Control Center', category: 'hub', icon: '🏯', path: '/warroom', keywords: ['war', 'room', 'command', 'center', 'dashboard', 'mission'] },
  { id: 'shield', title: 'Anti-Dilution Shield', subtitle: 'VC Term Sheet Calculator', category: 'hub', icon: '🛡️', path: '/shield', keywords: ['shield', 'anti', 'dilution', 'term', 'sheet', 'vc', 'calculator', 'equity'] },
  { id: 'sales', title: 'Sales Force', subtitle: 'Sales Pipeline & CRM', category: 'hub', icon: '💼', path: '/sales', keywords: ['sales', 'pipeline', 'crm', 'deals', 'revenue'] },
  { id: 'marketing', title: 'Marketing Ops', subtitle: 'Campaign Management', category: 'hub', icon: '📢', path: '/marketing', keywords: ['marketing', 'campaign', 'ads', 'promotion'] },
  { id: 'product', title: 'Product Lab', subtitle: 'Product Development', category: 'hub', icon: '🔬', path: '/product', keywords: ['product', 'lab', 'development', 'features'] },
  { id: 'finance', title: 'Finance Vault', subtitle: 'Financial Management', category: 'hub', icon: '💰', path: '/finance', keywords: ['finance', 'vault', 'money', 'budget', 'accounting'] },
  { id: 'hr', title: 'People Ops', subtitle: 'HR & Talent', category: 'hub', icon: '👥', path: '/hr', keywords: ['hr', 'people', 'talent', 'hiring', 'team'] },
  { id: 'legal', title: 'Legal Shield', subtitle: 'Contracts & Compliance', category: 'hub', icon: '⚖️', path: '/legal', keywords: ['legal', 'contracts', 'compliance', 'law'] },
  { id: 'analytics', title: 'Analytics Hub', subtitle: 'Data & Insights', category: 'hub', icon: '📊', path: '/analytics', keywords: ['analytics', 'data', 'insights', 'metrics', 'reports'] },
  { id: 'support', title: 'Support Desk', subtitle: 'Customer Support', category: 'hub', icon: '🎧', path: '/support', keywords: ['support', 'help', 'customer', 'tickets'] },
  { id: 'hubs', title: 'All Hubs', subtitle: 'Browse All Departments', category: 'hub', icon: '🏠', path: '/hubs', keywords: ['hubs', 'all', 'departments', 'browse'] },
  { id: 'action-theme', title: 'Toggle Theme', subtitle: 'Switch light/dark mode', category: 'action', icon: '🌓', keywords: ['theme', 'dark', 'light', 'mode', 'toggle'] },
  { id: 'action-sound', title: 'Toggle Sound', subtitle: 'Mute/unmute UI sounds', category: 'action', icon: '🔊', keywords: ['sound', 'audio', 'mute', 'unmute'] },
  { id: 'action-tour', title: 'Start Tour', subtitle: 'Restart onboarding tour', category: 'action', icon: '🎯', keywords: ['tour', 'onboarding', 'guide', 'help'] },
  { id: 'action-shortcuts', title: 'Keyboard Shortcuts', subtitle: 'View all shortcuts', category: 'action', icon: '⌨️', keywords: ['keyboard', 'shortcuts', 'hotkeys', 'keys'] },
  { id: 'setting-notifications', title: 'Notifications', subtitle: 'Manage notification preferences', category: 'setting', icon: '🔔', keywords: ['notifications', 'alerts', 'bell'] },
  { id: 'setting-profile', title: 'Profile Settings', subtitle: 'Edit your profile', category: 'setting', icon: '👤', keywords: ['profile', 'account', 'settings', 'user'] },
  { id: 'setting-presets', title: 'Theme Presets', subtitle: 'Change color theme', category: 'setting', icon: '🎨', keywords: ['theme', 'presets', 'colors', 'cyberpunk', 'ocean', 'forest', 'sunset', 'midnight'] },
]

export function fuzzyMatch(query: string, text: string): number {
  const q = query.toLowerCase()
  const t = text.toLowerCase()

  if (t.includes(q)) return 100

  const words = t.split(/\s+/)
  for (const word of words) {
    if (word.startsWith(q)) return 80
  }

  let qIdx = 0
  let score = 0
  for (let i = 0; i < t.length && qIdx < q.length; i++) {
    if (t[i] === q[qIdx]) {
      score += 10
      qIdx++
    }
  }

  if (qIdx === q.length) return score
  return 0
}

export function scoreResult(query: string, result: SearchResult): number {
  const titleScore = fuzzyMatch(query, result.title) * 2
  const subtitleScore = fuzzyMatch(query, result.subtitle)
  const keywordScores = result.keywords.map(k => fuzzyMatch(query, k))
  const maxKeywordScore = Math.max(...keywordScores, 0)

  return titleScore + subtitleScore + maxKeywordScore
}
