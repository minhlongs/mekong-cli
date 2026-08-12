# Mekong UI Design System

==Import==
All components available from _ds_bundle.js:
`import { Button, Card, Badge } from "@@ds-bundle";`

==Styling==
- Use `var(--*)` CSS custom properties (defined in styles.css)
- Color tokens: `--color-brand-*` (Mekong Blue), `--color-neutral-*`
- Semantic: `--bg-primary`, `--text-primary`, `--border-default`, `--accent`
- Spacing: `--spacing-1` through `--spacing-24` (4px grid)
- Radius: `--radius-sm/md/lg/xl/full`
- Motion: `--duration-fast/normal/slow`, `--ease-out`, `--ease-spring`

==Patterns==
- Buttons: CVA variants (default/secondary/ghost/danger) + sizes (sm/md/lg)
- Cards: variants (default/elevated/bordered) + CardHeader/CardContent/CardFooter
- Badges: idle/running/success/failed/warning/gain/loss
