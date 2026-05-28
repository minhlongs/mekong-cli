---
name: "source-command-tasks-todo"
description: "Manage project TODO items"
---

# source-command-tasks-todo

Use this skill when the user asks to run the migrated source command `tasks-todo`.

## Command Template

// turbo

# /todo - Task Manager

Quick TODO management without leaving Codex.

## Usage

```
/todo                    # List all
/todo add [task]        # Add new
/todo done [id]         # Mark complete
/todo priority [id]     # Set priority
```

## Codex Prompt Template

```
TODO management workflow:

Storage: .Codex/todo.json

Commands:
- list: Show all TODOs sorted by priority/due date
- add: Create new TODO with optional due date
- done: Mark TODO as complete
- priority: Set priority (high/medium/low)

TODO format:
{
  "id": "uuid",
  "task": "description",
  "priority": "high|medium|low",
  "due": "2024-01-20",
  "done": false,
  "created": "timestamp"
}

Display with emojis:
🔴 High priority
🟡 Medium priority
🟢 Low priority
✅ Completed
```

## Example Output

```
📋 TODOs (5 active)

🔴 #1 Fix login bug (due: today)
🔴 #2 Client meeting prep
🟡 #3 Update documentation
🟡 #4 Review PR #42
🟢 #5 Refactor utils

✅ Completed: 3 this week

/todo add "New task" to add
/todo done 1 to complete
```
