# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-06

### Added
- **Bidirectional Sync**: GitHub Projects V2 ↔ Local JSON storage
- **Last-Write-Wins**: Automatic conflict resolution based on timestamps
- **Interactive CLI**: User-friendly prompts for missing configuration
- **Dry Run Mode**: Preview sync actions without making changes
- **Error Recovery**: Retry logic with exponential backoff for transient failures
- **Input Validation**: Comprehensive validation for tokens, owners, paths
- **Structured Errors**: Clear error messages with recovery suggestions
- **E2E Testing**: Real-world GitHub API testing framework
- **TypeScript Support**: Full type safety with exported types

### Features
- GraphQL integration with GitHub Projects V2 API
- Atomic file writes with temp file + rename strategy
- Rate limit handling with automatic retry
- Token validation (supports ghp_, gho_, ghu_, ghs_, ghr_ prefixes)
- Environment variable support (GITHUB_TOKEN)
- gh CLI integration for authentication
- Progress reporting with detailed sync statistics
- JSON structure validation for data integrity

### Documentation
- Complete README with usage examples
- E2E testing guide with prerequisites
- API documentation for programmatic usage
- Troubleshooting guide

### Testing
- Unit tests for sync engine (4 scenarios)
- Mock integration tests for GraphQL layer
- E2E test script with real GitHub API
- CLI integration tests

## [Unreleased]

### Planned
- Manual conflict resolution UI
- Selective sync (filter by labels/status)
- Webhook support for real-time sync
- Multi-directional sync (multiple projects)
- Export to CSV/Markdown formats
- Progress bars for large projects
- Incremental sync (delta only)

[1.0.0]: https://github.com/agencyos/vibe-dev/releases/tag/v1.0.0
