export interface LayerData {
  id: string
  chapter: string
  role: string
  description: string
  icon: string
  commands: string[]
  cascadesTo: string[]
  entryPrompt: string
  color: string
}

export const LAYERS: LayerData[] = [
  {
    id: "founder",
    chapter: "始計 — Initial Calculations",
    role: "Founder / CEO",
    description: "Strategic vision, fundraising, OKRs, financial goals. The apex of the pyramid.",
    icon: "👑",
    // prettier-ignore
    commands: ["annual","quarterly","forecast","fundraise","swot","okr","kpi","goal-dashboard","portfolio","tier-pricing","branding","muc-tieu","bao-cao-tai-chinh","cofounder","raise","credits","launch"],
    cascadesTo: ["business"],
    entryPrompt: "Bạn là founder. Hôm nay muốn làm gì? Chiến lược, tài chính, hay mục tiêu?",
    color: "cyan-400",
  },
  {
    id: "business",
    chapter: "作戰 — Waging War",
    role: "Business Lead / GTM",
    description: "Sales, marketing, finance, HR, client ops. Revenue engine layer.",
    icon: "🏢",
    // prettier-ignore
    commands: ["sales","marketing","finance","pipeline","leadgen","client","crm","invoice","invoice-gen","expense","tax","contract","hr","email","close","revenue","cashflow","ads","social","seo","content","affiliate","nhan-su","khach-hang","doi-tac","hop-dong","chien-dich","ke-hoach-tiep-thi","ngan-sach","lich-trinh","phan-tich","danh-gia"],
    cascadesTo: ["product"],
    entryPrompt: "Layer kinh doanh. Sales, marketing, tài chính, hay nhân sự?",
    color: "blue-400",
  },
  {
    id: "product",
    chapter: "謀攻 — Attack by Stratagem",
    role: "Product Manager / Designer",
    description: "Roadmap, sprints, personas, proposals, demos. Bridge between biz and eng.",
    icon: "📦",
    // prettier-ignore
    commands: ["plan","brainstorm","scope","estimate","sprint","proposal","demo","competitor","persona","roadmap","pricing","feedback","retrospective","standup","handoff","du-an","bao-cao"],
    cascadesTo: ["engineering"],
    entryPrompt: "Layer sản phẩm. Roadmap, sprint, scope, hay brainstorm?",
    color: "purple-400",
  },
  {
    id: "engineering",
    chapter: "軍爭 — Military Contention",
    role: "Engineer / Tech Lead",
    description: "Code, build, test, deploy, review. The execution powerhouse.",
    icon: "⚙️",
    // prettier-ignore
    commands: ["cook","code","fix","debug","refactor","optimize","test","unit-test","e2e-test","integration-test","review","deploy","deploy-staging","deploy-prod","ship","arch","docs","docs-api","docs-arch","docs-changelog","docs-deploy","docs-onboard","docs-readme","api","schema","migrate","seed","component","vibe-code","vibe-cook","coverage","lint","typecheck","format","git","git-bisect","git-branch","git-cherry","git-merge","git-rebase","git-squash","git-stash","git-tag","pr","kanban","journal","watzup"],
    cascadesTo: ["ops"],
    entryPrompt: "Layer kỹ thuật. Cook, fix, test, review, hay deploy?",
    color: "green-400",
  },
  {
    id: "ops",
    chapter: "九變 — Nine Variations",
    role: "DevOps / Platform",
    description: "Audit, health, security, sync, environment. The foundation layer.",
    icon: "🔧",
    // prettier-ignore
    commands: ["audit","health","status","report","benchmark","security","env","init","install","setup-mcp","use-mcp","update","clean","rollback","smoke","sync-agent","sync-all","sync-antigravity","sync-artifacts","sync-browser","sync-editor","sync-mcp","sync-rules","sync-tasks","win-check","help","raas"],
    cascadesTo: [],
    entryPrompt: "Layer vận hành. Audit, health check, security, hay sync?",
    color: "orange-400",
  },
] as const
