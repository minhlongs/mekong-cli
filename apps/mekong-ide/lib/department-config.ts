/**
 * Department configuration — derived from tenants/*.json definitions.
 * Provides static department metadata (slug, name, icon, accent color).
 * Static list keeps the client bundle free from server-side fs reads.
 */

export interface DepartmentInfo {
  /** URL-safe slug, e.g. "marketing" */
  slug: string;
  /** Human-readable name, e.g. "Marketing" */
  name: string;
  /** Lucide icon name, e.g. "trending-up" */
  icon: string;
  /** Hex accent color from branding */
  accentColor: string;
  /** Short tagline shown on department cards */
  tagline: string;
}

/**
 * Static department registry derived from tenants/*.json.
 * Regenerate by running: node scripts/gen-department-config.js
 */
const DEPARTMENTS: DepartmentInfo[] = [
  { slug: "accounting",   name: "Accounting",   icon: "bar-chart-2",  accentColor: "#8B5CF6", tagline: "Financial records & reporting" },
  { slug: "analyst",      name: "Analyst",       icon: "bar-chart-2",  accentColor: "#8B5CF6", tagline: "Data analysis & insights" },
  { slug: "audit",        name: "Audit",         icon: "scale",        accentColor: "#6B7280", tagline: "Compliance & risk review" },
  { slug: "backend",      name: "Backend",       icon: "terminal",     accentColor: "#3B82F6", tagline: "API & server development" },
  { slug: "board",        name: "Board",         icon: "rocket",       accentColor: "#A855F7", tagline: "Strategic governance" },
  { slug: "business",     name: "Business",      icon: "users",        accentColor: "#EC4899", tagline: "Business operations" },
  { slug: "cdp",          name: "CDP",           icon: "pen-tool",     accentColor: "#F59E0B", tagline: "Customer data platform" },
  { slug: "code",         name: "Code",          icon: "terminal",     accentColor: "#3B82F6", tagline: "Code generation & review" },
  { slug: "compliance",   name: "Compliance",    icon: "scale",        accentColor: "#6B7280", tagline: "Regulatory compliance" },
  { slug: "content",      name: "Content",       icon: "pen-tool",     accentColor: "#F59E0B", tagline: "Content creation & strategy" },
  { slug: "data",         name: "Data",          icon: "bar-chart-2",  accentColor: "#8B5CF6", tagline: "Data pipelines & BI" },
  { slug: "design",       name: "Design",        icon: "palette",      accentColor: "#14B8A6", tagline: "UI/UX & brand design" },
  { slug: "engineering",  name: "Engineering",   icon: "terminal",     accentColor: "#3B82F6", tagline: "Full-stack development" },
  { slug: "finance",      name: "Finance",       icon: "trending-up",  accentColor: "#10B981", tagline: "Financial planning & analysis" },
  { slug: "founder",      name: "Founder",       icon: "rocket",       accentColor: "#A855F7", tagline: "Founder strategy & ops" },
  { slug: "growth",       name: "Growth",        icon: "trending-up",  accentColor: "#EF4444", tagline: "Growth experiments & loops" },
  { slug: "hr",           name: "HR",            icon: "users",        accentColor: "#EC4899", tagline: "People & culture" },
  { slug: "incident",     name: "Incident",      icon: "activity",     accentColor: "#DC2626", tagline: "Incident response & recovery" },
  { slug: "legal",        name: "Legal",         icon: "scale",        accentColor: "#6B7280", tagline: "Legal contracts & counsel" },
  { slug: "marketing",    name: "Marketing",     icon: "trending-up",  accentColor: "#EF4444", tagline: "Campaigns & brand growth" },
  { slug: "ops",          name: "Ops",           icon: "activity",     accentColor: "#DC2626", tagline: "Operations & automation" },
  { slug: "sales",        name: "Sales",         icon: "trending-up",  accentColor: "#EF4444", tagline: "Pipeline & revenue" },
  { slug: "security",     name: "Security",      icon: "activity",     accentColor: "#DC2626", tagline: "Security & threat modeling" },
  { slug: "venture",      name: "Venture",       icon: "rocket",       accentColor: "#A855F7", tagline: "Venture studio & dealflow" },
];

/** All departments sorted alphabetically */
export function getDepartments(): DepartmentInfo[] {
  return DEPARTMENTS;
}

/** Lookup a single department by slug; null if not found */
export function getDepartment(slug: string): DepartmentInfo | null {
  return DEPARTMENTS.find((d) => d.slug === slug) ?? null;
}
