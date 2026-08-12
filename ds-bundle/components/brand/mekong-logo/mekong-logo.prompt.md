# MekongLogo

**File:** `components/brand/mekong-logo/mekong-logo.html`
**Group:** `brand`
**Props:** `MekongLogoProps extends React.SVGAttributes<SVGSVGElement>`

## Variants
- `default`: base variant

## Usage
```jsx
import { MekongLogo } from "@@ds-bundle";

<MekongLogo variant="default" className="...">
  ...
</MekongLogo>
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
