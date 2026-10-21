export interface CommandItem {
  cmd: string
  desc: string
  action?: string
  path?: string
}

export interface CommandSuite {
  name: string
  icon: string
  binh_phap: string
  commands: CommandItem[]
}

export interface FlattenedCommand extends CommandItem {
  suite: string
  icon: string
  binh_phap: string
}

export interface CommandResult {
  success: boolean
  command?: string
  error?: string
  binh_phap?: string
  [key: string]: unknown
}

export interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onExecute?: (command: string, result: CommandResult) => void
}

export const COMMAND_SUITES: Record<string, CommandSuite> = {
  marketing: {
    name: 'Marketing', icon: '🔥', binh_phap: '謀攻篇',
    commands: [
      { cmd: '/ke-hoach-tiep-thi', desc: 'AI Marketing Plan Generator' },
      { cmd: '/seo', desc: 'SEO Strategy & Keywords' },
      { cmd: '/pr', desc: 'PR Campaign Creator' },
      { cmd: '/content', desc: 'Content Calendar' },
      { cmd: '/social', desc: 'Social Media Strategy' },
      { cmd: '/ads', desc: 'Ad Campaign Planner' },
      { cmd: '/branding', desc: 'Brand Guidelines' },
      { cmd: '/email', desc: 'Email Sequences' },
    ],
  },
  sales: {
    name: 'Sales', icon: '🛒', binh_phap: '作戰篇',
    commands: [
      { cmd: '/khach-hang', desc: 'Customer Research AI' },
      { cmd: '/crm', desc: 'CRM Setup' },
      { cmd: '/leadgen', desc: 'Lead Generation' },
      { cmd: '/pipeline', desc: 'Sales Pipeline' },
      { cmd: '/proposal', desc: 'Proposal Generator' },
      { cmd: '/pricing', desc: 'Pricing Analysis' },
      { cmd: '/demo', desc: 'Demo Builder' },
      { cmd: '/close', desc: 'Closing Playbook' },
    ],
  },
  finance: {
    name: 'Finance', icon: '💰', binh_phap: '計篇',
    commands: [
      { cmd: '/bao-cao-tai-chinh', desc: 'Financial Reports' },
      { cmd: '/ngan-sach', desc: 'Budget Planning' },
      { cmd: '/invoice', desc: 'Invoice Generator' },
      { cmd: '/cashflow', desc: 'Cashflow Analysis' },
      { cmd: '/tax', desc: 'Tax Planning' },
      { cmd: '/forecast', desc: 'Financial Forecasting' },
      { cmd: '/expense', desc: 'Expense Tracking' },
      { cmd: '/revenue', desc: 'Revenue Analysis' },
    ],
  },
  development: {
    name: 'Development', icon: '⚡', binh_phap: '九變篇',
    commands: [
      { cmd: '/refactor', desc: 'Code Refactoring' },
      { cmd: '/migrate', desc: 'Database Migration' },
      { cmd: '/api', desc: 'API Builder' },
      { cmd: '/component', desc: 'Component Generator' },
      { cmd: '/optimize', desc: 'Performance Optimization' },
      { cmd: '/security', desc: 'Security Audit' },
      { cmd: '/deploy:prod', desc: 'Deploy Production' },
      { cmd: '/rollback', desc: 'Rollback Deployment' },
    ],
  },
  testing: {
    name: 'Testing', icon: '🧪', binh_phap: '虛實篇',
    commands: [
      { cmd: '/test:unit', desc: 'Unit Tests' },
      { cmd: '/test:e2e', desc: 'E2E Tests' },
      { cmd: '/coverage', desc: 'Code Coverage' },
      { cmd: '/lint', desc: 'Lint Check' },
      { cmd: '/format', desc: 'Code Format' },
      { cmd: '/typecheck', desc: 'Type Check' },
      { cmd: '/audit', desc: 'Dependency Audit' },
      { cmd: '/benchmark', desc: 'Performance Benchmark' },
    ],
  },
  strategy: {
    name: 'Strategy', icon: '🎯', binh_phap: '始計篇',
    commands: [
      { cmd: '/swot', desc: 'SWOT Analysis' },
      { cmd: '/competitor', desc: 'Competitor Analysis' },
      { cmd: '/market', desc: 'Market Research' },
      { cmd: '/persona', desc: 'Customer Personas' },
      { cmd: '/roadmap', desc: 'Product Roadmap' },
      { cmd: '/kpi', desc: 'KPI Dashboard' },
      { cmd: '/retro', desc: 'Retrospective' },
      { cmd: '/quarterly', desc: 'Quarterly Review' },
    ],
  },
  vietnamese: {
    name: 'Vietnamese', icon: '🇻🇳', binh_phap: '地形篇',
    commands: [
      { cmd: '/phan-tich', desc: 'Phân Tích Thị Trường' },
      { cmd: '/bao-cao', desc: 'Báo Cáo Tự Động' },
      { cmd: '/du-an', desc: 'Quản Lý Dự Án' },
      { cmd: '/nhan-su', desc: 'Quản Lý Nhân Sự' },
      { cmd: '/hop-dong', desc: 'Tạo Hợp Đồng' },
      { cmd: '/lich-trinh', desc: 'Lịch Trình' },
      { cmd: '/muc-tieu', desc: 'Đặt Mục Tiêu' },
      { cmd: '/danh-gia', desc: 'Đánh Giá Hiệu Suất' },
    ],
  },
  sync: {
    name: 'Sync', icon: '🔄', binh_phap: '用間篇',
    commands: [
      { cmd: '/sync-agent', desc: 'Sync Agent Config' },
      { cmd: '/sync-rules', desc: 'Sync Rules' },
      { cmd: '/sync-tasks', desc: 'Sync Tasks' },
      { cmd: '/sync-mcp', desc: 'Sync MCP Servers' },
      { cmd: '/sync-all', desc: 'Sync Everything' },
    ],
  },
  newsletter: {
    name: 'Newsletter', icon: '📧', binh_phap: '火攻篇',
    commands: [
      { cmd: '/newsletter', desc: 'Newsletter Dashboard' },
      { cmd: '/newsletter:create', desc: 'Create New Newsletter' },
      { cmd: '/newsletter:edit', desc: 'Open Newsletter Editor' },
      { cmd: '/newsletter:ai-write', desc: 'AI Content Generator' },
      { cmd: '/newsletter:send', desc: 'Send Newsletter' },
      { cmd: '/newsletter:analytics', desc: 'View Analytics' },
      { cmd: '/newsletter:subscribers', desc: 'Manage Subscribers' },
      { cmd: '/newsletter:automations', desc: 'Email Automations' },
    ],
  },
  navigation: {
    name: 'Navigate', icon: '🚀', binh_phap: '行軍篇',
    commands: [
      { cmd: '/go:dashboard', desc: 'Go to Dashboard', action: 'navigate', path: '/dashboard' },
      { cmd: '/go:hubs', desc: 'Go to Hubs', action: 'navigate', path: '/hubs' },
      { cmd: '/go:analytics', desc: 'Go to Analytics', action: 'navigate', path: '/analytics' },
      { cmd: '/go:clients', desc: 'Go to Clients', action: 'navigate', path: '/clients' },
      { cmd: '/go:projects', desc: 'Go to Projects', action: 'navigate', path: '/projects' },
      { cmd: '/go:invoices', desc: 'Go to Invoices', action: 'navigate', path: '/invoices' },
      { cmd: '/go:marketing', desc: 'Go to Marketing', action: 'navigate', path: '/marketing' },
      { cmd: '/go:sales', desc: 'Go to Sales', action: 'navigate', path: '/sales' },
      { cmd: '/go:warroom', desc: 'Go to War Room', action: 'navigate', path: '/warroom' },
      { cmd: '/go:binhphap', desc: 'Go to Binh Pháp', action: 'navigate', path: '/binhphap' },
      { cmd: '/go:agents', desc: 'Go to Agents', action: 'navigate', path: '/agents' },
      { cmd: '/go:settings', desc: 'Go to Settings', action: 'navigate', path: '/settings' },
    ],
  },
}

export const ALL_COMMANDS: FlattenedCommand[] = Object.values(COMMAND_SUITES).flatMap(suite =>
  suite.commands.map(cmd => ({ ...cmd, suite: suite.name, icon: suite.icon, binh_phap: suite.binh_phap }))
)
