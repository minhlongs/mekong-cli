---
name: "source-command-worker-push"
description: "Push commits to remote with CI/CD verification"
---

# source-command-worker-push

Use this skill when the user asks to run the migrated source command `worker-push`.

## Command Template

# /worker-push — Worker Operation

Push and verify deployment.

1. `git push origin [branch]`
2. Monitor CI/CD pipeline
3. Verify deployment status
4. Report: Push/CI/Deploy status
