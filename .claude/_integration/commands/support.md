---
description: "Customer success — onboarding, feedback, support channels"
argument-hint: "[onboard|feedback|contact] [args]"
---

# /support — Customer Success

## Usage
```
/support onboard --check        # Show onboarding progress
/support onboard --step 1       # Mark step complete
/support feedback --nps 9       # Rate 0-10
/support feedback --bug "desc"  # Report bug
/support feedback --report      # Show all feedback
/support contact                # Show support channels
```

## Onboarding Steps
1. Set API Keys
2. Choose Agents
3. Run First Workflow
4. View Results
5. Subscribe

## Support Channels
- GitHub Issues: https://github.com/longtho638-jpg/mekong-cli/issues
- Email: support@mekongmind.com

## Implementation
- onboard: `node scripts/onboard.cjs --check|--step <N>`
- feedback: `node scripts/feedback.cjs --nps|--bug|--report`
