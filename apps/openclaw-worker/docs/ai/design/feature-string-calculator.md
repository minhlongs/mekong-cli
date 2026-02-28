---
phase: design
title: String Calculator Design
description: Design for the String Calculator utility
---

# Design & Architecture

## System Architecture

- **Component:** `StringCalculator` class or standalone `add` function.
- **Location:** `src/string-calculator.ts`.
- **Tests:** `test/string-calculator.test.ts`.

## Data Models

- **Input:** `string` (the numbers string).
- **Output:** `number` (the sum).
- **Error:** `Error` (thrown when negatives are found).

## API / Interface

```typescript
export function add(numbers: string): number;
```

## Logic Flow

1.  **Empty Check:** If input is empty, return 0.
2.  **Delimiter Parsing:**
    - Default delimiters: `,` and `\n`.
    - Custom delimiter format: `//[delimiter]\n[numbers]`.
3.  **Splitting:** Split string by delimiters.
4.  **Parsing:** Convert substrings to integers.
5.  **Validation:** Collect all negative numbers. If any exist, throw Error "negatives not allowed: [list]".
6.  **Summation:** Sum valid numbers.
7.  **Return:** Total sum.

## Security & Performance

- Input size is assumed to be reasonable for memory (not streaming gigabytes of numbers).
- No external dependencies required.
