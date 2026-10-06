# Design Guidelines — Dispute Resolution & Maritime Law Suite

## 1. Typography & Hierarchy
- **Primary Terminal Font**: Monospace font (JetBrains Mono / SF Mono / Consolas).
- **Header Structure**: Rich `Panel.fit` double border with cyan title and golden statutory citations.
- **Data Tables**: `box.ROUNDED` border styling with alternating cyan, yellow, and green column styles.

## 2. Color Palette & Semantics
- **Cyan (`#00FFFF`)**: Structural labels, procedural deadlines, and legal basis citations.
- **Green (`#00FF00`)**: Compliant thresholds, valid arbitration agreements, and enforceable claims.
- **Red (`#FF0000`)**: Statutorily invalid terms, overdue limitation periods, and void arbitration clauses.
- **Yellow / Gold (`#FFD700`)**: Monetary figures (VND, SDR), court fee calculations, and general average contribution ratios.

## 3. Human vs Machine Data Separation
- Terminal human output utilizes Rich formatted tables, panels, and colored badges.
- When `--json` is supplied, output uses `typer.echo(json.dumps(..., ensure_ascii=False, indent=2))` without any ANSI escape codes.
