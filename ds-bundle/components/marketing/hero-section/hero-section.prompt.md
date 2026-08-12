# HeroSection

**File:** `components/marketing/hero-section/hero-section.html`
**Group:** `marketing`
**Props:** `HeroSectionProps extends React.HTMLAttributes<HTMLElement>`

## Variants
- `default`: base variant

## Usage
```jsx
import { HeroSection } from "@@ds-bundle";

<HeroSection variant="default" className="...">
  ...
</HeroSection>
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
