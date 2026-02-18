# Project Changelog

## [Unreleased]

## [0.1.0] - 2026-02-19

### Added
- **AI DevKit Integration**: Installed `ai-devkit` CLI and configured `@ai-devkit/memory` MCP server.
- **Workflow Commands**: Imported `.claude/commands/` for structured development:
  - `/execute-plan`: Interactive plan execution.
  - `/code-review`: Local code review assistant.
  - `/new-requirement`: Requirement gathering workflow.
  - `/writing-test`: Test generation workflow.
- **Verification Feature**: Added `test-exec` feature (Source: `src/test-exec.ts`, Test: `test/test-exec.test.ts`) to validate the full AI DevKit lifecycle.
- **Intelligence Report**: Added `knowledge/ai-devkit-integration-intel.md` documenting the "Hybrid V" operational model (ClaudeKit Strategy + AI DevKit Tactics).
