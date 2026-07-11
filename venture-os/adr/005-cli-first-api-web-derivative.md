# ADR-005: CLI-First, API and Web as Derivatives

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

Should VentureOS be built as a web application, a CLI tool, or both?

## Decision

Build the CLI first. All core logic lives in CLI commands. API endpoints and web UI are wrappers over the same CLI logic (subprocess calls or library imports). The CLI is the reference implementation.

## Consequences

- **Easier:** Fastest path to a working system. Every AI agent (Claude Code, Codex, etc.) can drive it. No browser needed for operators.
- **Harder:** Web UX is constrained by CLI affordances (file-based workflow). Rich visualizations require a separate web layer.
- **Longevity:** CLIs outlive GUIs by decades. A pure web app needs a server, a browser, and JavaScript. A CLI works over SSH on a 1990s terminal.
- **What breaks if wrong:** If the web app becomes the primary interface, the CLI atrophies. Guard: never build a web feature that doesn't have a CLI equivalent first.
