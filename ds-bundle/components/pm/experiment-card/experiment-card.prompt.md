# ExperimentCard

**File:** `components/pm/experiment-card/experiment-card.html`
**Group:** `pm`
**Props:** `ExperimentCardProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `winning`: ...
- `losing`: ...
- `inconclusive`: ...
- `running`: ...
- `result`: ...

## Usage
```jsx
import { ExperimentCard } from "@@ds-bundle";

<ExperimentCard variant="default" className="...">
  ...
</ExperimentCard>
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
