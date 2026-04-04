"use client";

export default function Page() {
  return (
    <div className="flex flex-col gap-[var(--spacing-xl)] p-[var(--spacing-xl)]">
      <div>
        <h1 className="font-mono text-[var(--font-2xl)] font-bold text-[var(--text-primary)]">
          Entity Management
        </h1>
        <p className="mt-[var(--spacing-xs)] text-[var(--font-sm)] text-[var(--text-secondary)]">
          Corporate structure, cap table, and D&O insurance.
        </p>
      </div>
      <div className="grid grid-cols-4 gap-[var(--spacing-lg)]">
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Entities</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">3</span></div><div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Jurisdictions</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">2</span></div><div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">409A Date</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">2026-01</span></div><div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">D&O Active</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">Yes</span></div>
      </div>
      <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-xl)]">
        <p className="text-[var(--font-sm)] text-[var(--text-muted)]">
          Dashboard content loading...
        </p>
      </div>
    </div>
  );
}
