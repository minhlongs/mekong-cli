# Phase 7: Real-World End-to-End Testing Guide

## Overview

This guide walks you through testing the complete vibe-dev CLI with a real GitHub Project V2.

---

## Prerequisites

### 1. GitHub Personal Access Token

Create a token with **`project`** scope:

1. Go to https://github.com/settings/tokens/new
2. Select scopes:
   - ✅ `project` (Read/Write access to Projects)
   - ✅ `repo` (if using private repositories)
3. Generate token and save it securely

### 2. GitHub Project V2

Create a test project:

**For User Projects:**
```bash
# Via GitHub UI:
# 1. Go to https://github.com/users/YOUR_USERNAME/projects
# 2. Click "New project"
# 3. Select "Table" or "Board"
# 4. Note the project number (e.g., #1)
```

**For Organization Projects:**
```bash
# Via GitHub UI:
# 1. Go to https://github.com/orgs/YOUR_ORG/projects
# 2. Click "New project"
# 3. Select "Table" or "Board"
# 4. Note the project number (e.g., #5)
```

### 3. Sample Issues

Add 2-3 test issues to your project:

1. Create issues in a repository
2. Add them to your Project V2
3. Set different statuses/priorities

---

## Running the E2E Test

### Method 1: Using npm script

```bash
# Set your token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"

# Run test (User project)
npm run test:e2e YOUR_USERNAME 1

# Run test (Org project)
npm run test:e2e YOUR_ORG 5 true
```

### Method 2: Direct ts-node

```bash
GITHUB_TOKEN=ghp_xxx ts-node scripts/test-e2e-real-github.ts myuser 1
GITHUB_TOKEN=ghp_xxx ts-node scripts/test-e2e-real-github.ts myorg 5 true
```

---

## Test Scenarios

The E2E script runs 4 automated tests:

### Test 1: Initial Pull (GitHub → Local)
- **Action:** Fetches all tasks from GitHub Project V2
- **Expected:** Creates local JSON file with tasks
- **Verification:**
  - File `test-e2e-tasks.json` created
  - Task count matches GitHub project
  - Sample task data printed

### Test 2: No-Op Sync
- **Action:** Re-runs sync without changes
- **Expected:** No push/pull actions
- **Verification:**
  - `addedToLocal = 0`
  - `updatedLocal = 0`
  - `addedToRemote = 0`
  - `updatedRemote = 0`

### Test 3: Local Modification → Push
- **Action:** Modifies local task, syncs to GitHub
- **Expected:** Pushes changes to GitHub
- **Verification:**
  - Local task status/priority changed
  - `updatedRemote > 0`

### Test 4: Dry Run Mode
- **Action:** Plans changes but doesn't execute
- **Expected:** No actual push/pull
- **Verification:**
  - `actions.length > 0` (planned)
  - `updatedRemote = 0` (not executed)

---

## Manual Verification Steps

After automated tests pass, verify manually:

### 1. Check GitHub UI
```bash
# Open your project in browser
open "https://github.com/users/YOUR_USERNAME/projects/1"
# or
open "https://github.com/orgs/YOUR_ORG/projects/5"
```

Verify:
- Task status changed (from Test 3)
- Task priority changed to "high"

### 2. Modify in GitHub
1. Edit a task in GitHub UI (change status/priority)
2. Re-run the E2E test
3. Verify local file reflects the change

### 3. Conflict Resolution (Optional)
1. Modify same task in both GitHub and local file
2. Set different `updatedAt` timestamps
3. Run sync
4. Verify Last-Write-Wins logic (newer timestamp wins)

---

## Expected Output

```
🧪 Phase 7: Real-World End-to-End Test

═══════════════════════════════════════

📋 Test Configuration:
   Owner: myuser
   Project: #1
   Type: User
   Token: ghp_abc...
   Test File: /path/to/test-e2e-tasks.json

─────────────────────────────────────────
TEST 1: Initial Pull (GitHub → Local)
─────────────────────────────────────────

Initializing Sync Command...
Fetching remote tasks from myuser/1...
Reading local tasks from test-e2e-tasks.json...
Calculating sync actions...

--- Sync Report ---
⬇️  Pulled (Create): 3
⬇️  Pulled (Update): 0
⬆️  Pushed (Create): 0
⬆️  Pushed (Update): 0
-------------------

✅ Test 1 Results:
   Created Local Tasks: 3
   Errors: 0

📄 Local File Contents:
   Tasks: 3
   Epics: 0

   Sample Task:
     ID: I_12345
     Title: Test Task 1
     Status: pending
     Priority: medium

─────────────────────────────────────────
TEST 2: No-Op Sync (No Changes Expected)
─────────────────────────────────────────

--- Sync Report ---
⬇️  Pulled (Create): 0
⬇️  Pulled (Update): 0
⬆️  Pushed (Create): 0
⬆️  Pushed (Update): 0
-------------------

✅ Test 2 Results:
   Pulled: 0
   Pushed: 0

─────────────────────────────────────────
TEST 3: Local Modification → Push
─────────────────────────────────────────

✏️  Modified Local Task:
   Changed status: pending → active
   Changed priority → high
   Updated timestamp: 2026-02-06T11:30:00.000Z

--- Sync Report ---
⬇️  Pulled (Create): 0
⬇️  Pulled (Update): 0
⬆️  Pushed (Create): 0
⬆️  Pushed (Update): 1
-------------------

✅ Test 3 Results:
   Pushed Updates: 1
   Errors: 0

─────────────────────────────────────────
TEST 4: Dry Run Mode (No Side Effects)
─────────────────────────────────────────

--- Sync Report ---
(Dry run - no changes made)
-------------------

✅ Test 4 Results:
   Actions Planned: 1
   Actually Pushed: 0 (should be 0)

═══════════════════════════════════════
🎉 ALL TESTS PASSED
═══════════════════════════════════════

Summary:
  ✅ Initial Pull: Fetched tasks from GitHub
  ✅ No-Op Sync: No changes detected
  ✅ Local Push: Modified local → pushed to GitHub
  ✅ Dry Run: No side effects

📝 Manual Verification Steps:
  1. Open your GitHub Project V2 in browser
  2. Verify task status/priority changes are reflected
  3. Modify a task in GitHub UI
  4. Run this script again to verify pull works

🗑️  Cleanup: Delete test-e2e-tasks.json when done
```

---

## Troubleshooting

### Error: "Token is required"
```bash
# Make sure GITHUB_TOKEN is set
echo $GITHUB_TOKEN
# Should print: ghp_xxxxx
```

### Error: "Project not found"
```bash
# Verify project number
# User: https://github.com/users/USERNAME/projects/NUMBER
# Org: https://github.com/orgs/ORGNAME/projects/NUMBER
```

### Error: "Insufficient permissions"
```bash
# Token needs 'project' scope
# Regenerate token at: https://github.com/settings/tokens
```

### No tasks pulled
```bash
# Verify issues are added to the project
# GitHub Project V2 → Add items → Select issues
```

---

## Cleanup

```bash
# Delete test file after verification
rm test-e2e-tasks.json

# Optionally delete test project
# (Via GitHub UI: Project settings → Delete project)
```

---

## Next Steps After E2E Success

1. **Documentation**: Update main README with usage examples
2. **Publishing**: Prepare for npm publication
3. **CI/CD**: Add GitHub Actions workflow
4. **Error Handling**: Enhance based on edge cases discovered
5. **Features**: Add more sync strategies (manual conflict resolution, selective sync, etc.)

---

**Note:** This E2E test requires real GitHub credentials and will make actual API calls. Use a test account/project to avoid affecting production data.
