# Git Standards

Branch protection, commit convention, and workflow rules.

## Branch Protection (main)

Applied via `gh api repos/<owner>/<repo>/branches/main/protection`:

```json
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "guard-1-ci"},
      {"context": "guard-2-deploy"}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "required_linear_history": true,
  "allow_force_pushes": false
}
```

## Conventional Commits

Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`
Scopes: module/area name (optional)

Examples:
```
feat(api): add user authentication
fix(db): resolve migration ordering
refactor(hooks): extract shared logic
```

## Secrets Scan

Before every commit:
```bash
git diff --cached | grep -iE "(api[_-]?key|token|password|secret|credential)"
```
If found: BLOCK commit.

## CI Requirements

Guard 1 must pass before merge:
- `npm run type-check`
- `npm test`
- `npm run lint`
- `npm run build`
