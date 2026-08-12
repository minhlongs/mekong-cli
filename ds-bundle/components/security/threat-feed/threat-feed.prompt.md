# ThreatFeed

**File:** `components/security/threat-feed/threat-feed.html`
**Group:** `security`
**Props:** `ThreatFeedProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `critical`: ...
- `high`: ...
- `medium`: ...
- `low`: ...
- `info`: ...
- `severity`: ...

## Usage
```jsx
import { ThreatFeed } from "@@ds-bundle";

<ThreatFeed variant="default" className="...">
  ...
</ThreatFeed>
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
