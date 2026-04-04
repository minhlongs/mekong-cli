"use client";

export default function Page() {
  return (
    <div className="flex flex-col gap-[var(--spacing-xl)] p-[var(--spacing-xl)]">
      <div>
        <h1 className="font-mono text-[var(--font-2xl)] font-bold text-[var(--text-primary)]">API Documentation</h1>
        <p className="mt-[var(--spacing-xs)] text-[var(--font-sm)] text-[var(--text-secondary)]">Auto-generated OpenAPI reference documentation</p>
      </div>
      <div className="grid grid-cols-4 gap-[var(--spacing-lg)]">
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Endpoints</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">23</span></div>
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Schemas</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">45</span></div>
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Examples</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">67</span></div>
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Coverage</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">94%</span></div>
      </div>
      <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-xl)]">
        <p className="text-[var(--font-sm)] text-[var(--text-muted)]">Dashboard content loading...</p>
      </div>
    </div>
  );
}
