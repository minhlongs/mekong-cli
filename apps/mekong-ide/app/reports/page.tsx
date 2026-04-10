/**
 * Reports index page — /reports
 * Grid of all 22 business departments, each linking to /reports/{dept}/
 */
"use client";

import Link from "next/link";
import { Badge } from "@/components/ds";
import type { BadgeVariant } from "@/lib/types";

interface DepartmentCard {
  slug: string;
  label: string;
  description: string;
  badge: BadgeVariant;
  icon: string;
}

/** All 22 departments across the 6 Mekong layers */
const DEPARTMENTS: DepartmentCard[] = [
  { slug: "marketing", label: "Marketing", description: "Campaigns, content, brand performance", badge: "info", icon: "📣" },
  { slug: "finance", label: "Finance", description: "Budget, P&L, forecasts, expenses", badge: "success", icon: "💰" },
  { slug: "sales", label: "Sales", description: "Pipeline, deals, conversion metrics", badge: "trading", icon: "🎯" },
  { slug: "hr", label: "Human Resources", description: "Hiring, reviews, headcount planning", badge: "architect", icon: "👥" },
  { slug: "compliance", label: "Compliance", description: "Audits, risk, regulatory reports", badge: "audit", icon: "🔒" },
  { slug: "engineering", label: "Engineering", description: "Sprints, code quality, deployments", badge: "reasoning", icon: "⚙️" },
  { slug: "product", label: "Product", description: "Roadmap, feature velocity, user metrics", badge: "info", icon: "🚀" },
  { slug: "operations", label: "Operations", description: "Logistics, SLAs, process efficiency", badge: "warning", icon: "📦" },
  { slug: "legal", label: "Legal", description: "Contracts, IP, litigation tracking", badge: "audit", icon: "⚖️" },
  { slug: "strategy", label: "Strategy", description: "OKRs, competitive analysis, pivots", badge: "reasoning", icon: "🧭" },
  { slug: "vc", label: "VC Studio", description: "Deal flow, cap table, portfolio", badge: "success", icon: "🏦" },
  { slug: "growth", label: "Growth", description: "Acquisition, retention, LTV analysis", badge: "trading", icon: "📈" },
  { slug: "data", label: "Data & Analytics", description: "Dashboards, models, data quality", badge: "info", icon: "📊" },
  { slug: "security", label: "Security", description: "Vulnerabilities, incidents, posture", badge: "danger", icon: "🛡️" },
  { slug: "support", label: "Customer Support", description: "Tickets, CSAT, resolution times", badge: "warning", icon: "🎧" },
  { slug: "partnerships", label: "Partnerships", description: "BD deals, co-marketing, integrations", badge: "info", icon: "🤝" },
  { slug: "design", label: "Design", description: "UX research, design system, accessibility", badge: "architect", icon: "🎨" },
  { slug: "content", label: "Content", description: "Editorial calendar, SEO, performance", badge: "info", icon: "✍️" },
  { slug: "devops", label: "DevOps", description: "CI/CD, infra cost, uptime", badge: "reasoning", icon: "🔧" },
  { slug: "research", label: "Research", description: "Market research, competitor intel", badge: "audit", icon: "🔬" },
  { slug: "founder", label: "Founder", description: "Annual planning, fundraising, board", badge: "success", icon: "👑" },
  { slug: "trading", label: "Trading", description: "Signals, positions, algo performance", badge: "trading", icon: "📉" },
];

export default function ReportsIndexPage() {
  return (
    <div style={{ padding: "2rem", maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 className="m3-headline-large" style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
          Reports
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          {DEPARTMENTS.length} departments · Select a department to view available reports
        </p>
      </div>

      {/* Department grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: "1rem",
        }}
      >
        {DEPARTMENTS.map((dept) => (
          <Link
            key={dept.slug}
            href={`/reports/${dept.slug}`}
            style={{ textDecoration: "none" }}
          >
            <div
              style={{
                background: "var(--surface-elevated)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--md-sys-shape-corner-medium, 0.75rem)",
                padding: "1.25rem",
                cursor: "pointer",
                transition: "border-color 0.15s, background 0.15s",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor =
                  "var(--md-sys-color-primary, #6750A4)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor =
                  "var(--border-subtle)";
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.625rem" }}>
                <span style={{ fontSize: "1.5rem" }}>{dept.icon}</span>
                <Badge variant={dept.badge} label={dept.label} />
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.4 }}>
                {dept.description}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
