# @agencyos/vibe-dev

**🟢 Earth - Development Workflow Layer**

Bidirectional sync between GitHub Projects V2 and local JSON storage for task management workflows.

---

## Features

- ✅ **Bidirectional Sync**: GitHub Projects V2 ↔ Local JSON
- ✅ **Last-Write-Wins**: Automatic conflict resolution based on timestamps
- ✅ **Interactive CLI**: Prompts for missing configuration
- ✅ **Dry Run Mode**: Preview changes before execution
- ✅ **DevOps Metrics**: DORA and Engineering Velocity (Cycle Time) analytics
- ✅ **TypeScript**: Full type safety and IntelliSense support

---

## Installation

```bash
npm install @agencyos/vibe-dev
```

Or install globally:

```bash
npm install -g @agencyos/vibe-dev
```

---

## Quick Start

### 1. Get GitHub Personal Access Token

Create a token with **`project`** scope:
- Go to https://github.com/settings/tokens/new
- Select scopes: `project` (required), `repo` (optional)
- Save token securely

### 2. Run Sync

**Interactive Mode** (recommended for first use):
```bash
vibe sync
# Prompts for:
#   - GitHub Token
#   - Owner (username or org)
#   - Project Number
#   - Local file path
```

**Non-Interactive Mode** (for automation):
```bash
export GITHUB_TOKEN=ghp_xxxxx
vibe sync \
  --owner myuser \
  --number 1 \
  --path tasks.json
```

**Organization Project:**
```bash
vibe sync \
  --owner myorg \
  --org \
  --number 5 \
  --path team-tasks.json
```

### 3. Run DevOps Metrics

Analyze repository performance (DORA & Velocity):

```bash
# Auto-detects repo from current directory
vibe metrics

# Specify repo manually
vibe metrics --owner facebook --repo react --days 90

# Output as JSON for piping
vibe metrics --json > report.json
```

---

## Usage

### CLI Options

```
Usage: vibe sync [options]

Options:
  -t, --token <token>    GitHub Personal Access Token
  -o, --owner <owner>    Repository Owner or Organization
  -n, --number <number>  Project Number
  -p, --path <path>      Local file path (default: vibe-tasks.json)
  --org                  Treat owner as Organization
  --dry-run              Preview changes without executing
  --no-interactive       Disable interactive prompts (for CI/CD)
  -h, --help             Display help
```

### Metrics Command

```
Usage: vibe metrics [options]

Options:
  -o, --owner <owner>  Repository owner (e.g. facebook)
  -r, --repo <repo>    Repository name (e.g. react)
  -d, --days <days>    Analysis period in days (default: "30")
  --json               Output as JSON
  -h, --help           display help for command
```

### Environment Variables

```bash
# Set token via environment
export GITHUB_TOKEN=ghp_xxxxx

# Use in command
vibe sync --owner myuser --number 1
```

### Dry Run Mode

Preview sync actions without making changes:

```bash
vibe sync --dry-run
```

Output example:
```
--- Sync Report ---
⬇️  Pulled (Create): 3
⬇️  Pulled (Update): 1
⬆️  Pushed (Create): 0
⬆️  Pushed (Update): 2
📝 Actions Taken:
   - [PULL] New task from remote: "Implement auth"
   - [PULL] Updated task: "Fix bug" (status changed)
   - [PUSH] Updated task: "Add tests" (priority changed)
   - [PUSH] Updated task: "Refactor" (status changed)
```

---

## How It Works

### Sync Algorithm: Last-Write-Wins (LWW)

1. **Fetch Remote**: Get all tasks from GitHub Project V2
2. **Read Local**: Load tasks from local JSON file
3. **Compare Timestamps**: For each task, compare `updatedAt`
4. **Resolve Conflicts**:
   - **Remote Newer**: Pull changes to local
   - **Local Newer**: Push changes to GitHub
   - **Same Timestamp**: No action (in sync)
5. **Execute Actions**: Apply pull/push operations

### Data Model

**Task Fields:**
```typescript
{
  id: string;           // GitHub node ID or generated ID
  type: 'epic' | 'task' | 'subtask';
  title: string;
  status: 'pending' | 'active' | 'blocked' | 'done';
  priority: 'critical' | 'high' | 'medium' | 'low';
  createdAt: string;    // ISO 8601
  updatedAt: string;    // ISO 8601
  description?: string;
  parentId?: string;
  subtasks?: string[];
  labels?: string[];
  assignee?: string;
  githubIssueId?: number;
  githubIssueUrl?: string;
}
```

**Local Storage Format:**
```json
{
  "tasks": [...],
  "epics": [...]
}
```

---

## Programmatic Usage

```typescript
import { SyncCommand } from '@agencyos/vibe-dev';

const cmd = new SyncCommand();

const result = await cmd.execute({
  githubToken: 'ghp_xxxxx',
  owner: 'myuser',
  projectNumber: 1,
  localPath: 'tasks.json',
  isOrg: false,
  dryRun: false,
  autoResolve: true
});

console.log(`Pulled: ${result.addedToLocal + result.updatedLocal}`);
console.log(`Pushed: ${result.addedToRemote + result.updatedRemote}`);
console.log(`Errors: ${result.errors.length}`);
```

---

## Development

### Setup

```bash
git clone https://github.com/agencyos/vibe-dev.git
cd vibe-dev
npm install
```

### Build

```bash
npm run build
```

### Testing

**Unit Tests:**
```bash
npm run test:sync-engine   # Sync logic tests
npm run test:sync-down     # Pull tests
npm run test:sync-up       # Push tests
npm run test:cli           # CLI integration
```

**E2E Test** (requires GitHub credentials):
```bash
export GITHUB_TOKEN=ghp_xxxxx
npm run test:e2e myuser 1
```

See [docs/phase-07-e2e-testing-guide.md](./docs/phase-07-e2e-testing-guide.md) for details.

### Local Development

```bash
npm link
vibe sync --help
```

---

## Roadmap

- [ ] Manual conflict resolution UI
- [ ] Selective sync (filter by labels/status)
- [ ] Webhook support for real-time sync
- [ ] Multi-directional sync (multiple projects)
- [ ] Export to other formats (CSV, Markdown)
- [ ] CI/CD integration examples

---

## License

MIT

---

## Contributing

Contributions welcome! Please open an issue or PR.

---

## Support

- **Issues**: https://github.com/agencyos/vibe-dev/issues
- **Docs**: https://github.com/agencyos/vibe-dev/docs

---

**Built with ❤️ by AgencyOS**
