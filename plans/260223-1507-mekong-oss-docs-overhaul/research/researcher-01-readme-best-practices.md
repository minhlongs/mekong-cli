# Research: README & Mermaid Best Practices for OSS CLI

## Findings

### 1. High-Impact CLI README Structure
Modern CLI tools (like `gh`, `tview`, `fzf`) follow a "time-to-first-value" (TTFV) approach.
- **Header**: Name, version badges, and a 1-sentence "What is it?".
- **Visual Hook**: A high-quality SVG or GIF of the CLI in action (e.g., using `vhs` for terminal recording).
- **Quick Start**: 1-line install command + 1-line "run it" command.
- **Why this exists**: Solve the "Why me?" question before "How to use?".
- **The Core Sections**:
    - **Installation** (OS-specific instructions).
    - **Key Features** (Bullet points with code snippets).
    - **Architecture** (High-level Mermaid diagram).
    - **Configuration** (Env vars, config files).
    - **Contributing & License**.

### 2. Best-in-Class Examples
- **GitHub CLI (`gh`)**: Focuses on workflow integration. Sections: Installation, Usage (categorized), Customization (Aliases/Extensions).
- **Homebrew**: Focuses on community and installation safety. Sections: Requirements, Installation, Troubleshooting.
- **Charm Tools (`vhs`, `gum`)**: Heavy use of "Terminal Aesthetics" (badges, colorful examples).

## Key Patterns
- **Progressive Disclosure**: Detailed flags/subcommands moved to a separate `USAGE.md` or website; README stays focused on the "Happy Path".
- **Plan-Execute-Verify (PEV) Documentation**:
    - **Plan**: Define the Goal + Pre-conditions.
    - **Execute**: Show the transformation (Input -> Process -> Output).
    - **Verify**: Define "Success" (Exit codes, state changes, file presence).
- **Developer-Centric**: Include a "Development" section with `make build` or `npm install` instructions immediately.

## Mermaid Diagram Tips (v11+)
- **Flowchart TD/LR**: Still the most robust for pipelines. Use `subgraph` to isolate the PEV stages.
- **Node Styling**: Use CSS classes or `style` commands to differentiate between "Internal Agents" and "External APIs".
- **v11 Features**: Better support for icons (FontAwesome) and markdown-in-nodes.
- **Pipeline Visualization**:
    - Use `rect` or `subgraph` for "The Loop".
    - `A[User Goal] --> B{Plan}; B -->|Recipe| C(Execute); C --> D{Verify}; D -->|Fail| B; D -->|Success| E[Done];`

## Unresolved Questions
- Should we include a full reference of all 50+ commands in the main README or link to a separate `/docs/commands.md`? (Recommendation: Link out).
- Best tool for SVG terminal rendering in 2026 (likely an evolution of `vhs`).

Sources:
- [GitHub CLI README](https://github.com/cli/cli/blob/trunk/README.md)
- [Homebrew README](https://github.com/Homebrew/brew/blob/master/README.md)
- [Mermaid v11 Documentation](https://mermaid.js.org/intro/)
- [OSS README Best Practices (2025/2026)](https://github.com/matiassingers/awesome-readme)
