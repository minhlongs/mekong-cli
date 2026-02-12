---
# Trigger - when should this workflow run?
on:
  workflow_dispatch: # Manual trigger

# Alternative triggers (uncomment to use):
# on:
#   issues:
#     types: [opened, reopened]
#   pull_request:
#     types: [opened, synchronize]
#   schedule: daily  # Fuzzy daily schedule (scattered execution time)
#   # schedule: weekly on monday  # Fuzzy weekly schedule

# Permissions - what can this workflow access?
permissions:
  contents: read

# Outputs - what APIs and tools can the AI use?
safe-outputs:
  create-issue: # Creates issues (default max: 1)
    max: 5 # Optional: specify maximum number
  # create-agent-session:   # Creates GitHub Copilot agent sessions (max: 1)
  # create-pull-request: # Creates exactly one pull request
  # add-comment:   # Adds comments (default max: 1)
  #   max: 2             # Optional: specify maximum number
  # add-labels:
---

# tom-hum-test

Reply with "Hello World from GitHub Models via gh aw!". Provide a haiku about bandwidth quotas.
