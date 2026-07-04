import { expect, test, describe } from "bun:test";
import { parseMarkdown } from "../src/parser.js";

describe("Markdown Chunker Parser", () => {
  test("should parse markdown file and split into logical chunks by headers", () => {
    const md = `
# Title

Overview content here.

## Setup

Setup details.

### Configurations

Config content.
    `.trim();

    const chunks = parseMarkdown("test-file.md", md);

    expect(chunks.length).toBe(3);

    // Overview chunk
    expect(chunks[0].title).toBe("Title");
    expect(chunks[0].h1).toBe("Title");
    expect(chunks[0].h2).toBeNull();
    expect(chunks[0].parentHeaders).toEqual([]);
    expect(chunks[0].content).toBe("# Title\n\nOverview content here.");

    // Setup chunk
    expect(chunks[1].title).toBe("Setup");
    expect(chunks[1].h1).toBe("Title");
    expect(chunks[1].h2).toBe("Setup");
    expect(chunks[1].parentHeaders).toEqual(["Title"]);
    expect(chunks[1].content).toBe("## Setup\n\nSetup details.");

    // Configurations chunk
    expect(chunks[2].title).toBe("Configurations");
    expect(chunks[2].h1).toBe("Title");
    expect(chunks[2].h2).toBe("Setup");
    expect(chunks[2].h3).toBe("Configurations");
    expect(chunks[2].parentHeaders).toEqual(["Title", "Setup"]);
    expect(chunks[2].content).toBe("### Configurations\n\nConfig content.");
  });

  test("should handle content before any headers correctly", () => {
    const md = `
This is initial content before H1.
Second line.

# First Header
Hello.
    `.trim();

    const chunks = parseMarkdown("README.md", md);
    expect(chunks.length).toBe(2);

    expect(chunks[0].title).toBe("README.md");
    expect(chunks[0].content).toBe("This is initial content before H1.\nSecond line.");
    expect(chunks[0].parentHeaders).toEqual([]);
    expect(chunks[0].h1).toBeNull();

    expect(chunks[1].title).toBe("First Header");
    expect(chunks[1].content).toBe("# First Header\nHello.");
    expect(chunks[1].h1).toBe("First Header");
  });

  test("should ignore headers inside code blocks", () => {
    const md = `
# Main Title

Here is a code block:
\`\`\`python
# This is a comment in Python, not a header
def foo():
    pass
\`\`\`

## Section 2
Text.
    `.trim();

    const chunks = parseMarkdown("code.md", md);
    expect(chunks.length).toBe(2);

    expect(chunks[0].title).toBe("Main Title");
    expect(chunks[0].content).toContain("This is a comment in Python");
    expect(chunks[0].h2).toBeNull();

    expect(chunks[1].title).toBe("Section 2");
    expect(chunks[1].h1).toBe("Main Title");
    expect(chunks[1].h2).toBe("Section 2");
  });

  test("should strip YAML frontmatter correctly", () => {
    const md = `
---
title: Doc Title
description: Setup guide
---

# Setup

Some content.
    `.trim();

    const chunks = parseMarkdown("setup.md", md);
    expect(chunks.length).toBe(1);
    expect(chunks[0].title).toBe("Setup");
    expect(chunks[0].content).toBe("# Setup\n\nSome content.");
  });

  test("should handle duplicate header names correctly in parent headers", () => {
    const md = `
# Setup

## Verification

### Setup

Details of sub setup.
    `.trim();

    const chunks = parseMarkdown("duplicate.md", md);
    expect(chunks.length).toBe(3);

    // Setup H1 chunk
    expect(chunks[0].title).toBe("Setup");
    expect(chunks[0].parentHeaders).toEqual([]);

    // Verification H2 chunk
    expect(chunks[1].title).toBe("Verification");
    expect(chunks[1].parentHeaders).toEqual(["Setup"]);

    // Setup H3 chunk (with H2 parent)
    expect(chunks[2].title).toBe("Setup");
    expect(chunks[2].parentHeaders).toEqual(["Setup", "Verification"]);
  });
});
