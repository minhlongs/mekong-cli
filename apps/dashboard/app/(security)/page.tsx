"use client";

import { VulnCard } from "@mekong/ui/components/security/vuln-card";
import { ComplianceGauge } from "@mekong/ui/components/security/compliance-gauge";
import { ThreatFeed } from "@mekong/ui/components/security/threat-feed";
import { PolicyStatus } from "@mekong/ui/components/security/policy-status";
import { IncidentTimeline } from "@mekong/ui/components/security/incident-timeline";
import { AccessMatrix } from "@mekong/ui/components/security/access-matrix";

const mockVulns = [
  { cve: "CVE-2026-1234", severity: "critical" as const, component: "openssl 3.1.0", slaHours: 24, status: "In Progress" },
  { cve: "CVE-2026-5678", severity: "high" as const, component: "lodash 4.17.21", slaHours: 72, status: "Triaged" },
  { cve: "CVE-2026-9012", severity: "medium" as const, component: "axios 1.6.0", slaHours: 168, status: "Open" },
  { cve: "CVE-2026-3456", severity: "low" as const, component: "debug 4.3.4", slaHours: 720, status: "Backlog" },
];

const mockThreats = [
  { time: "14:23", type: "Brute force attempt on SSH", source: "45.33.32.156", severity: "high" as const },
  { time: "14:21", type: "SQL injection blocked", source: "WAF/Cloudflare", severity: "critical" as const },
  { time: "14:18", type: "Certificate expiry warning", source: "cert-monitor", severity: "medium" as const },
  { time: "14:15", type: "New device login", source: "IAM/Okta", severity: "info" as const },
  { time: "14:12", type: "DDoS mitigation active", source: "WAF/Cloudflare", severity: "high" as const },
  { time: "14:08", type: "Secrets scan clean", source: "GitHub Advanced Security", severity: "info" as const },
];

const mockPolicies = [
  { name: "Acceptable Use Policy", status: "active" as const, lastReview: "2026-01-15" },
  { name: "Incident Response Plan", status: "active" as const, lastReview: "2026-02-20" },
  { name: "Data Classification Policy", status: "draft" as const, lastReview: "2025-11-01" },
  { name: "Remote Access Policy", status: "expired" as const, lastReview: "2025-06-10" },
];

const mockIncident = [
  { name: "Detect", status: "done" as const, duration: "2m" },
  { name: "Triage", status: "done" as const, duration: "8m" },
  { name: "Contain", status: "active" as const, duration: "15m" },
  { name: "Remediate", status: "pending" as const },
  { name: "Postmortem", status: "pending" as const },
];

const mockRoles = ["Admin", "Engineer", "Analyst", "Viewer"];
const mockSystems = ["AWS", "GitHub", "Okta", "Jira", "Snowflake"];
const mockPerms: Record<string, Record<string, "allow" | "deny" | "na">> = {
  Admin: { AWS: "allow", GitHub: "allow", Okta: "allow", Jira: "allow", Snowflake: "allow" },
  Engineer: { AWS: "allow", GitHub: "allow", Okta: "deny", Jira: "allow", Snowflake: "deny" },
  Analyst: { AWS: "deny", GitHub: "deny", Okta: "deny", Jira: "allow", Snowflake: "allow" },
  Viewer: { AWS: "deny", GitHub: "deny", Okta: "deny", Jira: "deny", Snowflake: "na" },
};

export default function SecurityDashboard() {
  return (
    <div className="flex flex-col gap-[var(--spacing-xl)] p-[var(--spacing-xl)]">
      <h1 className="font-mono text-[var(--font-2xl)] font-bold text-[var(--text-primary)]">
        Security Operations
      </h1>

      {/* Compliance Gauges */}
      <div className="grid grid-cols-3 gap-[var(--spacing-lg)]">
        <ComplianceGauge framework="SOC2" score={87} maxScore={100} />
        <ComplianceGauge framework="SOX" score={72} maxScore={100} />
        <ComplianceGauge framework="ISO27001" score={91} maxScore={100} />
      </div>

      {/* Incident Response */}
      <IncidentTimeline steps={mockIncident} />

      {/* Threat Feed + Vulns */}
      <div className="grid grid-cols-2 gap-[var(--spacing-lg)]">
        <ThreatFeed events={mockThreats} />
        <div className="flex flex-col gap-[var(--spacing-md)]">
          {mockVulns.map((v) => (
            <VulnCard key={v.cve} {...v} />
          ))}
        </div>
      </div>

      {/* Policy Status */}
      <PolicyStatus policies={mockPolicies} />

      {/* Access Matrix */}
      <AccessMatrix roles={mockRoles} systems={mockSystems} permissions={mockPerms} />
    </div>
  );
}
