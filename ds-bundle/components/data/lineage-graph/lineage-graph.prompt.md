# LineageGraph

**File:** `components/data/lineage-graph/lineage-graph.html`
**Group:** `data`
**Props:** `LineageGraphProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `type`: ...
- `source`: ...
- `transform`: ...
- `target`: ...

## Usage
```jsx
import { LineageGraph } from "@@ds-bundle";

<LineageGraph variant="default" className="...">
  ...
</LineageGraph>
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
