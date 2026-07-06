---
id: hello-world
name: "Hello World Script"
category: build
version: 0.1.0
description: Create a minimal hello world Python script with a main guard.
max_retries: 3
---

# Hello World Script

Create a minimal Python hello world script that prints "Hello, World!" to stdout.

## Steps

1. **Write file** — Create `hello.py` with a print statement and `if __name__ == "__main__"` guard
2. **Verify syntax** — Run `python -m py_compile hello.py` to confirm valid Python

## Verification

- `hello.py` exists and contains `print("Hello," World!")`
- `python hello.py` outputs `Hello, World!` exactly
