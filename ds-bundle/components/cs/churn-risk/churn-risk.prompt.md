# ChurnRisk

**File:** `components/cs/churn-risk/churn-risk.html`
**Group:** `cs`
**Props:** `ChurnRiskProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `default`: base variant

## Usage
```jsx
import { ChurnRisk } from "@@ds-bundle";

<ChurnRisk variant="default" className="...">
  ...
</ChurnRisk>
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
