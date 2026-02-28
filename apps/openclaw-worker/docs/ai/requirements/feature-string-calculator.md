---
phase: requirements
title: String Calculator Requirements
description: Implement a String Calculator following TDD Kata rules
---

# Requirements & Problem Understanding

## Problem Statement
**What problem are we solving?**

- We need a utility to sum numbers provided in a string format, handling various delimiters and edge cases.
- This serves as a validation exercise for the AI DevKit workflow.

## Goals & Objectives
**What do we want to achieve?**

- **Primary:** Implement a `add(numbers: string): number` function.
- **Secondary:** Demonstrate TDD workflow using AI DevKit structure.

## User Stories & Use Cases

- As a developer, I want to pass an empty string and get 0.
- As a developer, I want to pass "1" and get 1.
- As a developer, I want to pass "1,2" and get 3.
- As a developer, I want to handle newlines as delimiters ("1\n2,3" -> 6).
- As a developer, I want to support custom delimiters ("//;\n1;2" -> 3).
- As a developer, I want an exception thrown for negative numbers.

## Success Criteria
**How will we know when we're done?**

- All TDD cases pass.
- Code is clean and typed.
- Tests are comprehensive.

## Constraints & Assumptions

- Language: TypeScript.
- Test Framework: Vitest.
