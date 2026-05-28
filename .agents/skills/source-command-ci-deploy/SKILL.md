---
name: "source-command-ci-deploy"
description: "Production deployment with safety checks"
---

# source-command-ci-deploy

Use this skill when the user asks to run the migrated source command `ci-deploy`.

## Command Template

// turbo

# /deploy - Production Deployment

Deploy to production with pre-flight checks.

## Usage

```
/deploy [environment]
/deploy --staging
/deploy --prod
```

## Codex Prompt Template

```
Deployment workflow:

1. Pre-flight Checks:
   ✅ All tests passing
   ✅ No uncommitted changes
   ✅ On correct branch (main/master)
   ✅ CI/CD green
   ✅ No security vulnerabilities

2. Build:
   - Run production build
   - Verify build succeeds
   - Check bundle size

3. Deploy:
   - Staging: vercel deploy
   - Production: vercel deploy --prod

4. Post-deploy:
   - Verify deployment URL
   - Run smoke tests
   - Check monitoring

5. Report:
   - Deployment URL
   - Build time
   - Bundle size
   - Status
```

## Example Output

```
🚀 Deploying to Production

✅ Pre-flight: All checks pass
✅ Build: 45s (bundle: 1.2MB)
✅ Deployed: https://app.agencyos.io

Post-deploy:
- ✅ Health check: OK
- ✅ API: Responding
- ✅ DB: Connected

🎉 Production deployment complete!
```
