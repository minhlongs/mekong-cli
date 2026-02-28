     1→---
     2→stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type']
     3→inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-260218.md']
     4→workflowType: 'prd'
     5→classification:
     6→  projectType: 'cli_tool'
     7→  domain: 'Developer Productivity'
     8→  complexity: 'Low'
     9→  projectContext: 'greenfield'
    10→---
    11→
    12→# Product Requirements Document - Advanced CLI Calculator
    13→
    14→**Author:** Macbookprom1
    15→**Date:** 260218
    16→
    17→## Executive Summary
    18→
    19→The **Advanced CLI Calculator** is a developer-focused terminal utility designed to replace context-switching to browser-based converters. It combines standard arithmetic with specialized developer functions (unit conversions, hex/binary math, timestamp parsing) in a single, pipe-friendly binary. Targeted at software engineers, it aims to reduce friction in daily coding workflows by keeping calculations within the terminal environment.
    20→
    21→### What Makes This Special
    22→
    23→Unlike standard system calculators (`bc`, python REPL), this tool features a **Rich TUI Tape** for visual history while maintaining strict **Unix Pipeability** for scripting. It differentiates itself through **Domain-Specific Awareness**—understanding pixel-to-rem conversions, color manipulation, and epoch timestamps out of the box—and an **Extensible Plugin System** allowing users to define custom logic in Wasm/JS.
    24→
    25→## Project Classification
    26→
    27→*   **Type:** CLI Tool
    28→*   **Domain:** Developer Productivity
    29→*   **Complexity:** Low
    30→*   **Context:** Greenfield
    31→
    32→## Success Criteria
    33→
    34→### User Success
    35→*   **Zero Context Switching:** Users can perform common dev calculations (px->rem, hex math) without leaving their terminal.
    36→*   **Speed:** Calculations are performed faster than opening a browser tab or GUI app.
    37→*   **Retention:** Users alias `calc` to this tool and use it daily.
    38→
    39→### Business Success
    40→*   **Adoption:** 1,000+ GitHub stars within 3 months of launch.
    41→*   **Ecosystem:** 5+ community-contributed plugins within 6 months.
    42→*   **Distribution:** Accepted into major package managers (Homebrew, npm, cargo).
    43→
    44→### Technical Success
    45→*   **Performance:** Startup time < 50ms (perceptible "instant" execution).
    46→*   **Reliability:** 100% test coverage for core arithmetic and conversion logic.
    47→*   **Portability:** Single binary distribution for macOS, Linux, and Windows.
    48→
    49→### Measurable Outcomes
    50→*   **Time Saved:** Average of 15 seconds saved per conversion vs. browser lookup.
    51→*   **Usage:** Average of 5+ invocations per active user per day.
    52→
    53→## Product Scope
    54→
    55→### MVP - Minimum Viable Product
    56→*   **Core Math:** Standard arithmetic (+, -, *, /) and scientific functions.
    57→*   **Dev Conversions:** Px/Rem, Hex/RGB, Epoch/Date.
    58→*   **TUI Tape:** Scrollable history of recent calculations.
    59→*   **Pipe Support:** Ability to pipe input in and output out (JSON/Text).
    60→*   **Config:** Basic YAML configuration for defaults (e.g., base pixel size).
    61→
    62→### Growth Features (Post-MVP)
    63→*   **Plugin System:** Wasm-based plugin architecture for community extensions.
    64→*   **Cloud Sync:** Sync history and config across machines.
    65→*   **Graphing:** ASCII-based charting for simple data arrays.
    66→
    67→### Vision (Future)
    68→*   The standard-issue calculator for the modern terminal stack (replacing `bc`).
    69→*   Integrated directly into IDE terminals and CI/CD pipelines.
    70→
    71→## User Journeys
    72→
    73→### 1. Sarah - The CSS Refinement (Frontend Developer)
    74→*   **Opening:** Sarah is deep in a Vim session refactoring a legacy CSS file. She finds hardcoded pixel values and hex codes that need standardizing to `rem` and a new color palette.
    75→*   **Rising Action:** She considers opening Chrome to find a converter but remembers the context switch will break her flow. She opens the `calc` TUI pane alongside her code.
    76→*   **Climax:** She types `16px to rem` -> `1rem`. She then types `#3b82f6 darken 10%` -> `#2563eb`. She uses the "tape" feature to scroll back and copy previous results directly into her buffer.
    77→*   **Resolution:** She finishes the refactor in record time without ever leaving her terminal window.
    78→
    79→### 2. Mike - The Log Detective (Backend Developer)
    80→*   **Opening:** Mike is investigating a production incident. The logs are full of epoch timestamps and opaque Base64 strings.
    81→*   **Rising Action:** He pipes the log line into the tool: `echo "1708260000" | calc to date`.
    82→*   **Climax:** The tool outputs `2024-02-18T12:40:00Z`. He then sees a weird auth token, pipes it `echo "..." | calc b64d`, and sees the decoded JSON immediately.
    83→*   **Resolution:** He identifies the expired token issue in seconds, fix confirmed via the tool's quick math check on the expiry delta.
    84→
    85→### 3. Sam - The Toolsmith (Plugin Developer)
    86→*   **Opening:** Sam needs a specific calculation: a "Fibonacci backoff" generator for a retry script. The tool doesn't have it built-in.
    87→*   **Rising Action:** Instead of writing a separate Python script, Sam writes a 5-line JavaScript function `fib(n)` in `~/.calc/plugins/fib.js`.
    88→*   **Climax:** Sam restarts `calc`. The new `fib(10)` function is auto-detected and available with autocomplete.
    89→*   **Resolution:** Sam publishes the plugin to the community repo, helping others.
    90→
    91→### Journey Requirements Summary
    92→
    93→*   **Sarah's Journey:** Requirements for **Rich TUI**, **Unit Conversion Logic** (px/rem), **Color Math** (hex/rgb), and **Clipboard Integration**.
    94→*   **Mike's Journey:** Requirements for **Stdin/Stdout Piping**, **Epoch/Date Parsing**, **Base64 Decoding**, and **Instant Startup**.
    95→*   **Sam's Journey:** Requirements for **Plugin Architecture** (loading external scripts), **Hot Reloading** (or fast restart), and **Function Autodiscovery**.
    96→
    97→## Innovation & Novel Patterns
    98→
    99→### Detected Innovation Areas
   100→
   101→*   **Hybrid TUI/Pipe Architecture:** Most tools are either interactive TUI apps (hard to script) or pure CLI utilities (no visual history). `calc` innovates by detecting its context: rich "Tape" UI when TTY is present, pure JSON/Text stream when piped. This solves the "visual vs. automation" trade-off.
   102→*   **Context-Aware Dev Math:** Unlike `bc` or scientific calculators, `calc` treats "16px" and "#fff" as first-class citizens, reducing the cognitive load of translating dev concepts into raw numbers.
   103→*   **Wasm Plugin Sandbox:** Allowing users to write logic in Rust/Go/JS and run it safely in a calculator without recompiling the binary is a significant shift from "scriptable" configs.
   104→
   105→### Market Context & Competitive Landscape
   106→
   107→*   **`bc` / `dc`:** The standard, but archaic syntax and no dev-specific units.
   108→*   **Python/Node REPL:** Powerful but slow startup (>100ms) and requires verbose syntax (`import datetime`).
   109→*   **Numbat:** Excellent physical unit support, but less focused on web-dev specifics (CSS units, JSON manipulation).
   110→*   **Browser Console:** The current default for most devs, but requires context switching (mouse, tab management).
   111→
   112→### Validation Approach
   113→
   114→*   **"The Alt-Tab Test":** Measure if users stop Alt-Tabbing to Chrome for simple conversions. Success = 0 browser opens for "px to rem".
   115→*   **Startup Latency:** Must feel instantaneous (<50ms). If it lags, users will revert to `bc` or mental math.
   116→
   117→### Risk Mitigation
   118→
   119→*   **TUI Compatibility:** Terminals vary wildly. **Mitigation:** Robust feature detection and a "dumb mode" fallback.
   120→*   **Plugin Security:** Wasm provides a sandbox, but infinite loops in plugins could freeze the main thread. **Mitigation:** Strict timeout/gas limits on plugin execution.
   121→
## CLI Tool Specific Requirements

### Project-Type Overview

As a `cli_tool`, the calculator must balance interactive usability with strict unix-philosophy compliance. It operates in two distinct modes based on `isatty` detection.

### Technical Architecture Considerations

*   **Binary Distribution:** Single static binary (Go/Rust) to ensure 0-dependency installation.
*   **Startup Time:** Strict budget of <50ms to rival `ls` or `cat`.
*   **State Management:** Stateless by default; history is persisted to `~/.calc_history` only in TUI mode.

### Command Structure

*   **Usage:** `calc [expression] [flags]`
*   **Modes:**
    *   `Interactive`: Launched when no args provided.
    *   `One-Shot`: `calc "1 + 1"` prints "2".
    *   `Pipe`: `echo "1 + 1" | calc` prints "2".
*   **Flags:**
    *   `--json`: Output result as JSON object.
    *   `--debug`: Show parsing AST.
    *   `--version`: Show version.

### Output Formats

*   **Standard (TTY):** Human-readable, colored output. `2 rem` (where 'rem' might be dimmed).
*   **Raw (Pipe):** `2 rem` (plain text, no colors).
*   **JSON:** `{"value": 2, "unit": "rem", "raw": "2rem"}`.

### Configuration Schema

*   **Location:** `~/.config/calc/config.yaml`
*   **Format:**
    ```yaml
    defaults:
      base_pixel: 16
      theme: "dark"
    plugins:
      - "~/.calc/plugins/my-math.wasm"
    aliases:
      "g": "9.8 m/s^2"
    ```

### Scripting Support

*   **Exit Codes:**
    *   `0`: Success.
    *   `1`: Parse Error (invalid syntax).
    *   `127`: Plugin Error.
*   **Shebang Support:** Ability to write `#!/usr/bin/env calc` scripts.
