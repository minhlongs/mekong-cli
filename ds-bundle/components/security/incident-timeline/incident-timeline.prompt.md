# IncidentTimeline

**File:** `components/security/incident-timeline/incident-timeline.html`
**Group:** `security`
**Props:** `IncidentTimelineProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `done`: ...
- `active`: ...
- `pending`: ...
- `status`: ...

## Usage
```jsx
import { IncidentTimeline } from "@@ds-bundle";

<IncidentTimeline variant="default" className="...">
  ...
</IncidentTimeline>
```

## Styling
- Classes use `var(--*)` CSS custom properties from `styles.css`
- Color tokens: `--color-brand-*`, `--color-neutral-*`, `--color-*-500/600`
- Semantic: `--bg-primary`, `--text-primary`, `--border-default`, `--accent`
- Spacing: `--spacing-1` through `--spacing-24` (4px grid)
- Radius: `--radius-sm/md/lg/xl/full`
- Motion: `--duration-fast/normal/slow`, `--ease-out`, `--ease-spring`

## Notes
Rendered via esbuild bundle (`_ds_bundle.js`). React 19 + CVA patterns.
