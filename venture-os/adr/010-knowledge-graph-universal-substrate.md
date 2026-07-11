# ADR-010: Knowledge Graph as Universal Knowledge Substrate

**Status:** Accepted
**Date:** 2026-07-10
**Deciders:** OpenClaw CTO

## Context

How should VentureOS store and query research findings, precedents, methodologies, market data, and cross-venture learnings? Options: flat files, tagged documents, relational database, graph database, knowledge graph.

## Decision

A lightweight knowledge graph where every piece of knowledge is a typed node with edges to other nodes. Implemented as plain-text files (one node = one markdown file) with a graph layer on top. Graph queries traverse file references + explicit edge declarations. For scale: optional SQLite FTS index for full-text search + adjacency list for graph traversal.

Node types: market, methodology, precedent, technology, financial, legal, people. Edge types: contradicts, supports, supersedes, references, part_of, analogous_to.

## Consequences

- **Easier:** One format for everything. Research outputs feed directly into the graph. Decisions cite graph nodes. Templates pull from graph queries.
- **Harder:** Graph maintenance (no orphan nodes, edge validity). Mitigated by periodic hygiene workflows.
- **Longevity:** Markdown files with YAML frontmatter are readable forever. The graph layer is a convenience index — the source of truth is the files themselves.
- **What breaks if wrong:** If the knowledge graph becomes a proprietary database, you've traded composability for query speed. The graph is an index OVER plain-text files, not a replacement for them.
