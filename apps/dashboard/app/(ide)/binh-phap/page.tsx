"use client";
export default function Page() {
  return (
    <div className="flex flex-col gap-[var(--spacing-xl)] p-[var(--spacing-xl)]">
      <div><h1 className="font-mono text-[var(--font-2xl)] font-bold text-[var(--text-primary)]">Binh Phap Topology</h1><p className="mt-[var(--spacing-xs)] text-[var(--font-sm)] text-[var(--text-secondary)]">3D AGI topology</p></div>
      <div className="grid grid-cols-4 gap-[var(--spacing-lg)]">
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Groups</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">7</span></div>
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Dimensions</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">3</span></div>
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Self-Improve</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">Active</span></div>
        <div className="flex flex-col gap-[var(--spacing-xs)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Score</span><span className="font-mono text-[var(--font-xl)] font-bold text-[var(--text-primary)]">78%</span></div>
      </div>
      <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-xl)]"><p className="text-[var(--font-sm)] text-[var(--text-muted)]">Dashboard content loading...</p></div>
    </div>
  );
}
