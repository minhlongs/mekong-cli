# Deployment Automation for Plugin Documentation

This guide covers automated deployment of plugin documentation using CI/CD.

---

## Overview

The plugin documentation system supports automated deployment via:

1. **GitHub Actions** — Deploy to GitHub Pages on merge to main
2. **Cloudflare Pages** — Edge CDN with preview deployments
3. **MkDocs Material** — Static site generation

---

## GitHub Pages Deployment

### Prerequisites

1. Enable GitHub Pages in repository settings:
   - Go to Settings → Pages
   - Source: GitHub Actions

2. The `.github/workflows/plugin-docs.yml` workflow will automatically deploy.

### Workflow Steps

```yaml
name: Plugin Documentation

on:
  push:
    paths:
      - 'packages/**/plugin.json'
      - 'scripts/plugin-docs/**'

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev
      - name: Generate documentation
        run: |
          python scripts/plugin-docs/generate.py --plugins-dir packages
      - name: Validate
        run: |
          python scripts/plugin-docs/validate.py docs/plugins
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: plugin-docs
          path: docs/plugins/
```

The `peaceiris/actions-gh-pages` step then deploys the artifact to GitHub Pages.

---

## Cloudflare Pages

### Setup

1. Connect repository to Cloudflare Pages
2. Build command: `python scripts/plugin-docs/build.py`
3. Build output directory: `docs/plugins`
4. Environment variables: none required

### Preview Deployments

Cloudflare Pages automatically creates preview deployments for PRs. Plugin docs are available at:

- Production: `https://docs.mekongmind.com/plugins/`
- Preview: `https://<branch>--docs.mekongmind.com/plugins/`

---

## MkDocs Material Site

For a full documentation site (not just plugin docs), use MkDocs:

### Installation

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

### Local Development

```bash
mkdocs serve -f docs/mkdocs.yml
```

Opens at http://localhost:8000 with live reload.

### Production Build

```bash
mkdocs build -f docs/mkdocs.yml
```

Output in `site/` directory.

### Deployment

Push to any static hosting:

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy --force

# Or build and deploy manually
mkdocs build
# Upload site/ to your hosting provider
```

---

## Multi-Language Deployment

### Vietnamese Documentation

The system supports i18n via separate template files:

```
templates/
├── index.md              # English (default)
├── index.vi.md           # Vietnamese
├── commands.md
├── commands.vi.md
└── ...
```

Generate Vietnamese docs:

```bash
python scripts/plugin-docs/generate.py --lang vi --output docs/plugins/vi
```

Deploy to `/vi/` path on your site:

```
https://docs.mekongmind.com/vi/plugins/zalo-oa/
```

Configure language switcher in `docs/mkdocs.yml`:

```yaml
extra:
  alternate:
    - name: English
      link: /plugins/
      lang: en
    - name: Tiếng Việt
      link: /vi/plugins/
      lang: vi
```

---

## Versioned Documentation

Support multiple plugin versions:

```bash
# Generate for specific version
python scripts/plugin-docs/generate.py --version 1.2.3 -o docs/plugins/v1.2.3
```

Create a version selector in your site:

```html
<select onchange="window.location.href='/plugins/' + this.value + '/'">
  <option value="latest">Latest (1.2.3)</option>
  <option value="1.2.3">1.2.3</option>
  <option value="1.2.2">1.2.2</option>
</select>
```

---

## Automated Index Generation

The `build.py` script generates `index.md` listing all plugins:

```bash
python scripts/plugin-docs/build.py --plugins-dir docs/plugins
```

Output includes a markdown table:

| Plugin | Version | Description | Category |
|--------|---------|-------------|----------|
| Hello World | 1.0.0 | Minimal plugin demonstrating basic command registration | examples |

---

## CI/CD Best Practices

### Cache Dependencies

In GitHub Actions:

```yaml
- name: Cache pip
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### Deploy Only on Changes

Check if generated docs differ from committed:

```yaml
- name: Check for changes
  id: changes
  run: |
    git diff --quiet docs/plugins/ || echo "changed=true" >> $GITHUB_OUTPUT
- name: Deploy
  if: steps.changes.outputs.changed == 'true'
```

### Rate Limiting

If you have many plugins, generate in parallel:

```bash
# Modify generate.py to use ThreadPoolExecutor
python scripts/plugin-docs/generate.py --parallel 8
```

---

## Security Considerations

### No Secrets in Docs

The generator strips or redacts:
- API keys
- Database URLs
- Secret tokens

Ensure `plugin.json` doesn't contain secrets. Use environment variables.

### Validate All Inputs

The validator ensures:
- No broken links (internal)
- Proper markdown syntax
- Required files present

Add custom rules for your organization's standards.

---

## Monitoring

### Build Health

Track these metrics:
- Build duration (target: < 2 min for 50 plugins)
- Number of validation errors/warnings
- Deployment success rate

### Alerts

Set up GitHub Actions notifications for:
- Build failures
- Validation errors on PRs
- Deployment failures

---

## Rollback

If a deployment introduces issues:

1. **GitHub Pages**: Roll back to previous commit
2. **Cloudflare Pages**: Use "Deploys" tab to rollback
3. **Manual**: Re-deploy previous version from Git history

```bash
git checkout v1.0.0 docs/plugins/
mkdocs build
# Deploy to hosting
```

---

## Troubleshooting

### Build Fails with Template Error

```bash
# Verify templates syntax
python -c "from jinja2 import Environment, FileSystemLoader; Environment(loader=FileSystemLoader('scripts/plugin-docs/templates'))"
```

### Generated Docs Not Updated

Clear caches:

```bash
rm -rf docs/plugins/*
python scripts/plugin-docs/generate.py --clean
```

### Deploy Permissions

GitHub Actions needs:
- `contents: read` (checkout)
- `pages: write` (deploy)
- `id-token: write` (OIDC, if using)

Configure in repository Settings → Actions → General → Workflow permissions.

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cloudflare Pages Documentation](https://developers.cloudflare.com/pages/)
- [MkDocs Material Theme](https://squidfunk.github.io/mkdocs-material/)

---

## Support

- Issues: <https://github.com/mekongcli/mekong-cli/issues>
- Discord: `#docs` channel
