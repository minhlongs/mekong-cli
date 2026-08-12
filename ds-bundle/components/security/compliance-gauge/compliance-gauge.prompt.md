# ComplianceGauge

**File:** `components/security/compliance-gauge/compliance-gauge.html`
**Group:** `security`
**Props:** `ComplianceGaugeProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `framework`: ...
- `transition`: ...

## Usage
```jsx
import { ComplianceGauge } from "@@ds-bundle";

<ComplianceGauge variant="default" className="...">
  ...
</ComplianceGauge>
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
