---
name: "source-command-utils-search"
description: "Search codebase with smart filtering"
---

# source-command-utils-search

Use this skill when the user asks to run the migrated source command `utils-search`.

## Command Template

// turbo

# /search - Smart Code Search

Search codebase with context-aware results.

## Usage

```
/search [query]
/search --function [name]
/search --type [type-name]
/search --todo
```

## Codex Prompt Template

```
Smart search workflow:

1. Parse Query:
   - Identify search type (text/function/type/etc)
   - Apply filters

2. Execute Search:
   - Use ripgrep for speed
   - Include context (3 lines before/after)
   - Exclude node_modules, .git, etc

3. Rank Results:
   - Exact matches first
   - Definition > Usage
   - Recent files prioritized

4. Format Output:
   - File path with line number
   - Syntax highlighted snippet
   - Quick navigation links

Limit to top 10 results by default.
```

## Example Output

```
🔍 Search: "authenticate"

Found 8 matches:

1. src/auth/service.ts:42
   def authenticate(user, password):
       """Main authentication logic"""

2. src/api/handlers.ts:88
   const result = await authenticate(credentials)

3. tests/test_auth.py:15
   def test_authenticate_success():

...

📊 8 matches in 5 files
```
