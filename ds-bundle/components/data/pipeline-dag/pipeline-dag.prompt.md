# PipelineDag

**File:** `components/data/pipeline-dag/pipeline-dag.html`
**Group:** `data`
**Props:** `PipelineDagProps extends React.HTMLAttributes<HTMLDivElement>`

## Variants
- `running`: ...
- `success`: ...
- `failed`: ...
- `pending`: ...
- `status`: ...

## Usage
```jsx
import { PipelineDag } from "@@ds-bundle";

<PipelineDag variant="default" className="...">
  ...
</PipelineDag>
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
