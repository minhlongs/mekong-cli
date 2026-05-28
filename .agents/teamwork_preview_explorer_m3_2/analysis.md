# AST Symbol Extraction Layer Design (Milestone M3: SQLite & AST)

This document provides a comprehensive technical analysis and design specification for the AST Symbol Extraction layer (`src/indexer.rs`) in the Anti-Gravity 2.0 Hybrid Runtime workspace. 

---

## 1. Summary of Findings

- **Core Goal**: Extract structural symbols (functions, structs, classes, methods, traits) from repository files (`.rs`, `.py`, `.js`, `.ts`, `.tsx`, `.jsx`) with high precision, mapping their line spans and identifier names for indexing inside `.git/antigravity/session.db`.
- **Parsing Architecture**: We propose a **Dual-Track Parser Architecture**:
  1. **Primary Track**: Compile-time or dynamically initialized `tree-sitter` (version 0.20) syntax queries.
  2. **Fallback Track**: A robust, self-contained Regex Pattern Matching parser using standard library features and brace/indentation-matching heuristics.
- **Trade-offs**: Adding C-based grammar crates (`tree-sitter-rust`, `tree-sitter-python`, etc.) can introduce serious compilation and linking issues on Mac Apple Silicon (macOS arm64), especially when dynamic linking or compiler flags mismatch. A robust fallback is essential for build-time fault tolerance.

---

## 2. Tree-Sitter Symbol Extraction API (version 0.20)

### 2.1. Basic Execution Pipeline
To parse a code file and extract structural symbols using `tree-sitter`, the system follows these steps:
1. **Initialize the Parser**: Create an instance of `tree_sitter::Parser`.
2. **Set Language**: Load and configure the target language grammar (e.g. `parser.set_language(tree_sitter_rust::language())?`).
3. **Generate the Syntax Tree (AST)**: Parse the source string to retrieve a `tree_sitter::Tree`.
4. **Compile Queries**: Construct a `tree_sitter::Query` containing S-expressions specifying nodes to capture.
5. **Execute Query**: Use `tree_sitter::QueryCursor` to run the query against the root node of the tree.
6. **Extract Captures**: Iterate over matches and process specific captures to resolve names, kinds, and line coordinates.

### 2.2. Resolving Name vs. Declaration Nodes (The Capture Problem)
An essential detail when writing tree-sitter queries is that a query returns multiple captures per match. 
For example, in the S-expression:
```query
(function_item name: (identifier) @name) @function
```
For a single function, the query engine matches both the name node (`@name`) and the whole function declaration block (`@function`).
- **Symbol Name**: Extracted from the source code slice corresponding to the `@name` node.
- **Symbol Range (Start/End Lines)**: Extracted from the line range of the parent declaration node (`@function`).

If we conflate the two captures, we will either record the name of the function as the entire source body, or record the span of the function as only the single line where the identifier is written. The parsing logic must keep a map or inspect capture names dynamically to group `@name` and `@declaration` nodes correctly.

---

## 3. Build Implications of Language Crates on macOS Apple Silicon

Adding language-specific crates (like `tree-sitter-rust`, `tree-sitter-python`, `tree-sitter-typescript`) introduces complex compilation dependencies:

| Implication Factor | Risk Analysis & Details |
|--------------------|-------------------------|
| **C/C++ Compilation Overhead** | Tree-sitter grammars are compiled from large generated C/C++ parser source files (`parser.c`, `scanner.c`). Compiling them adds significant compile-time overhead (often 30s+ per language crate). |
| **Xcode Command Line Tools** | Compiling C sources in Rust build scripts uses the `cc` crate, which relies on `clang` on macOS. In headless, CI, or clean developer setups missing Xcode Command Line Tools, the compilation will fail immediately. |
| **Architecture Mismatch (arm64 vs x86_64)** | macOS Apple Silicon compilation requires targets compatible with `aarch64-apple-darwin`. If build tools or dynamic linking paths configure compiler targets incorrectly, build-time linking errors occur (e.g., mismatching architectures). |
| **ABI Version Mismatches** | The core `tree-sitter` crate (version 0.20) must match the grammar versions exactly. If a grammar crate targets a different ABI version (e.g., ABI 13 vs ABI 14), `set_language` will return runtime initialization errors. |

### 3.1. Recommendation: The Dual-Track Fallback Strategy
Given these risks, we recommend:
1. **Conditional Feature Flags**: Introduce features in `Cargo.toml` (e.g. `[features] tree-sitter-grammars = ["tree-sitter-rust", "tree-sitter-python"]`).
2. **Robust Regex Fallback**: Write a native pattern-matching parser in Rust using the `regex` crate (which is already a dependency and is pure Rust, building instantly and reliably on Mac Apple Silicon).
3. **Graceful Degradation**: If the grammar-specific parser fails to compile or is disabled, the indexer falls back to regex-based extraction. This ensures that `cargo check` and `cargo test` build immediately on any developer laptop.

---

## 4. Target AST Nodes & Tree-Sitter Query Patterns

For each target language, we recommend compiling the following `tree-sitter` queries. They are optimized for version 0.20 to identify structures, names, and spans:

### 4.1. Rust (`.rs`)
```query
;; Find function definitions
(function_item name: (identifier) @name) @function

;; Find struct definitions
(struct_item name: (type_identifier) @name) @struct

;; Find enum definitions
(enum_item name: (type_identifier) @name) @enum

;; Find traits
(trait_item name: (type_identifier) @name) @trait

;; Find impl blocks (extracting the type being implemented)
(impl_item type: (type_identifier) @name) @impl
```

### 4.2. Python (`.py`)
```query
;; Find classes
(class_definition name: (identifier) @name) @class

;; Find global or nested functions
(function_definition name: (identifier) @name) @function
```
*Note: In Python, methods can be distinguished from standalone functions by checking if the parent/ancestor of a `function_definition` node is a `class_definition` node.*

### 4.3. JavaScript / TypeScript (`.js`, `.ts`, `.tsx`, `.jsx`)
```query
;; Find class declarations
(class_declaration name: (identifier) @name) @class

;; Find named functions
(function_declaration name: (identifier) @name) @function

;; Find class method definitions
(method_definition name: (property_identifier) @name) @method

;; Find arrow functions or function expressions assigned to variables
(lexical_declaration 
  (variable_declarator 
    name: (identifier) @name 
    value: [(arrow_function) (function_expression)])) @function
```

---

## 5. Robust Regex Pattern-Matching Fallback Design

When tree-sitter parsers are unavailable, the indexer falls back to a regex-based parser. To provide accurate start and end lines, we implement a **signature parser** coupled with **block-scanning heuristics**:

### 5.1. Target Regex Patterns

- **Rust**:
  - Functions: `^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?(?:const\s+)?(?:async\s+)?fn\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Structs: `^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?struct\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Enums: `^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?enum\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Traits: `^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?trait\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Impls: `^\s*impl(?:\s*<[^>]+>)?\s+([a-zA-Z_][a-zA-Z0-9_]*)`

- **Python**:
  - Classes: `^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Functions/Methods: `^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)`

- **JS/TS**:
  - Classes: `^\s*(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Named Functions: `^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)`
  - Arrow Functions: `^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z_][a-zA-Z0-9_]*)\s*=>`
  - Methods: `^\s*(?:async\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{`

### 5.2. Brace & Indentation Block Scanning Heuristics

To find the `end_line` of a symbol when parsing with regex:

1. **Brace-Matching Heuristic (Rust, JS, TS)**:
   - Begin at the line containing the definition match.
   - Scan subsequent lines character-by-character.
   - Keep a counter: increment for every open brace `{`, decrement for every close brace `}`.
   - Once the counter returns to `0` (and we have seen at least one open brace), the current line is marked as the `end_line`.
   - If braces are unbalanced or don't close, fallback to `start_line`.

2. **Indentation-Matching Heuristic (Python)**:
   - Identify the indentation level (number of leading spaces/tabs) of the matched definition line.
   - Scan subsequent lines.
   - Skip empty lines and lines containing only comments (`#`).
   - The block ends when a non-empty, non-comment line is encountered with an **equal or lesser** indentation level than the definition line.
   - The line immediately preceding this change is marked as the `end_line`.

---

## 6. Structure of Parsing Logic in `src/indexer.rs`

Below is the concrete, clean design of the code structure for `src/indexer.rs`, illustrating how the dual-track system is orchestrated:

```rust
use std::path::Path;
use anyhow::{Result, Context};
use regex::Regex;

#[derive(Debug, Clone)]
pub struct Symbol {
    pub path: String,
    pub hash: String,
    pub name: String,
    pub kind: String,
    pub start_line: usize,
    pub end_line: usize,
}

/// Dynamic entry point to parse a file and extract symbols
pub fn extract_symbols_from_file(
    file_path: &Path,
    content: &str,
    hash: &str,
) -> Result<Vec<Symbol>> {
    let relative_path = file_path.to_string_lossy().to_string();
    let ext = file_path.extension().and_then(|e| e.to_str()).unwrap_or("");

    // Step 1: Attempt Tree-sitter extraction if enabled
    #[cfg(feature = "tree-sitter-grammars")]
    {
        match extract_symbols_via_tree_sitter(&relative_path, content, hash, ext) {
            Ok(symbols) => return Ok(symbols),
            Err(err) => {
                eprintln!(
                    "⚠️ Tree-sitter failed for {}, falling back to regex: {:?}",
                    relative_path, err
                );
            }
        }
    }

    // Step 2: Fallback to robust Regex extraction
    extract_symbols_via_regex(&relative_path, content, hash, ext)
}

// =========================================================================
// Track A: Tree-Sitter Parser Implementation (Requires compile-time grammars)
// =========================================================================
#[cfg(feature = "tree-sitter-grammars")]
fn extract_symbols_via_tree_sitter(
    path: &str,
    content: &str,
    hash: &str,
    ext: &str,
) -> Result<Vec<Symbol>> {
    use tree_sitter::{Parser, Query, QueryCursor};

    let (lang, query_str) = match ext {
        "rs" => (tree_sitter_rust::language(), r#"
            (function_item name: (identifier) @name) @function
            (struct_item name: (type_identifier) @name) @struct
            (enum_item name: (type_identifier) @name) @enum
            (trait_item name: (type_identifier) @name) @trait
            (impl_item type: (type_identifier) @name) @impl
        "#),
        "py" => (tree_sitter_python::language(), r#"
            (class_definition name: (identifier) @name) @class
            (function_definition name: (identifier) @name) @function
        "#),
        "js" | "jsx" | "ts" | "tsx" => (tree_sitter_typescript::language_typescript(), r#"
            (class_declaration name: (identifier) @name) @class
            (function_declaration name: (identifier) @name) @function
            (method_definition name: (property_identifier) @name) @method
            (lexical_declaration (variable_declarator name: (identifier) @name value: [(arrow_function) (function_expression)])) @function
        "#),
        _ => return Ok(Vec::new()), // Unsupported file format for Tree-sitter
    };

    let mut parser = Parser::new();
    parser.set_language(lang).context("Failed to load tree-sitter language")?;

    let tree = parser.parse(content, None)
        .context("Failed to generate tree-sitter syntax tree")?;
    let root_node = tree.root_node();

    let query = Query::new(lang, query_str).context("Failed to compile tree-sitter query")?;
    let mut cursor = QueryCursor::new();
    let matches = cursor.matches(&query, root_node, content.as_bytes());

    let mut symbols = Vec::new();
    
    for m in matches {
        let mut symbol_name = String::new();
        let mut kind = String::new();
        let mut start_line = 0;
        let mut end_line = 0;

        for capture in m.captures {
            let node = capture.node;
            let capture_name = &query.capture_names()[capture.index as usize];

            if capture_name == "name" {
                symbol_name = node.utf8_text(content.as_bytes())?.to_string();
            } else {
                // This is the declaration capture (e.g. "function", "struct")
                kind = capture_name.to_string();
                start_line = node.start_position().row + 1; // Convert to 1-indexed
                end_line = node.end_position().row + 1;
            }
        }

        if !symbol_name.is_empty() && !kind.is_empty() {
            symbols.push(Symbol {
                path: path.to_string(),
                hash: hash.to_string(),
                name: symbol_name,
                kind,
                start_line,
                end_line,
            });
        }
    }

    Ok(symbols)
}

// =========================================================================
// Track B: Fallback Regex Parser Implementation
// =========================================================================
fn extract_symbols_via_regex(
    path: &str,
    content: &str,
    hash: &str,
    ext: &str,
) -> Result<Vec<Symbol>> {
    let lines: Vec<&str> = content.lines().collect();
    let mut symbols = Vec::new();

    // Load appropriate regular expressions based on extension
    let rules = match ext {
        "rs" => vec![
            ("function", Regex::new(r"^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?(?:const\s+)?(?:async\s+)?fn\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("struct", Regex::new(r"^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?struct\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("enum", Regex::new(r"^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?enum\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("trait", Regex::new(r"^\s*(?:pub\s+)?(?:pub\([^)]+\)\s+)?trait\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("impl", Regex::new(r"^\s*impl(?:\s*<[^>]+>)?\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
        ],
        "py" => vec![
            ("class", Regex::new(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("function", Regex::new(r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
        ],
        "js" | "jsx" | "ts" | "tsx" => vec![
            ("class", Regex::new(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("function", Regex::new(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)")?),
            ("function", Regex::new(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z_][a-zA-Z0-9_]*)\s*=>")?),
            ("method", Regex::new(r"^\s*(?:async\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{")?),
        ],
        _ => return Ok(Vec::new()), // Unsupported extension
    };

    for (i, line) in lines.iter().enumerate() {
        for (kind, regex) in &rules {
            if let Some(captures) = regex.captures(line) {
                let name = captures.get(1).map(|m| m.as_str().to_string()).unwrap_or_default();
                if name.is_empty() {
                    continue;
                }

                let start_line = i + 1;
                let mut end_line = start_line;

                // Execute block-finding heuristics
                if ext == "py" {
                    end_line = find_python_block_end(&lines, i);
                } else {
                    end_line = find_brace_block_end(&lines, i);
                }

                symbols.push(Symbol {
                    path: path.to_string(),
                    hash: hash.to_string(),
                    name,
                    kind: kind.to_string(),
                    start_line,
                    end_line,
                });
                break; // Stop matching rule if one matches for this line
            }
        }
    }

    Ok(symbols)
}

/// Brace matching search to find the end line of a C-style or Rust-style declaration block
fn find_brace_block_end(lines: &[&str], start_idx: usize) -> usize {
    let mut brace_count = 0;
    let mut has_seen_open_brace = false;

    for (i, line) in lines.iter().enumerate().skip(start_idx) {
        for ch in line.chars() {
            if ch == '{' {
                brace_count += 1;
                has_seen_open_brace = true;
            } else if ch == '}' {
                brace_count -= 1;
            }
        }
        if has_seen_open_brace && brace_count <= 0 {
            return i + 1;
        }
    }
    start_idx + 1 // Fallback to start line if brace matching fails
}

/// Indentation checking search to find the end line of a Python declaration block
fn find_python_block_end(lines: &[&str], start_idx: usize) -> usize {
    let start_line = lines[start_idx];
    let start_indent = get_indentation_level(start_line);
    let mut last_valid_line = start_idx;

    for (i, line) in lines.iter().enumerate().skip(start_idx + 1) {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue; // Skip empty and comment lines
        }

        let current_indent = get_indentation_level(line);
        if current_indent <= start_indent {
            // Block ended when encountering line with same or less indentation
            return last_valid_line + 1;
        }
        last_valid_line = i;
    }
    last_valid_line + 1
}

/// Calculate leading space indentation level
fn get_indentation_level(line: &str) -> usize {
    line.chars().take_while(|c| c.is_whitespace()).count()
}
```

---

## 7. Verification Method

To verify the symbol parsing logic works correctly:
1. **Unit Tests**:
   - Write mock files (Rust, Python, JS) as strings, pass them to `extract_symbols_from_file`, and assert that the correct names, kinds, and lines are returned.
   - Specifically test brace-matching edges: functions with multiple nested curly braces inside (e.g. loops, blocks) and verify `end_line` aligns exactly with the outer-most closing brace.
   - Specifically test Python indentation edges: classes containing methods, and functions containing multi-line strings or docstrings.
2. **Benchmark Comparison**:
   - Parse large files (e.g., standard libraries or complex local source files) under both AST query modes and regex modes, comparing parsing latency (targeting < 1ms per file).
