---
name: "source-command-code-tdd-implement"
description: "Implement feature using TDD methodology"
---

# source-command-code-tdd-implement

Use this skill when the user asks to run the migrated source command `code-tdd-implement`.

## Command Template

// turbo

# /tdd-implement - TDD Implementation

Full TDD implementation from requirements to refactored code.

## Usage

```
/tdd-implement [feature-description]
```

## Codex Prompt Template

```
TDD Implementation workflow:

1. Analyze Requirements:
   - Parse feature description
   - Identify testable behaviors
   - Define acceptance criteria

2. Write Tests First (RED):
   - Create test file: tests/test_{feature}.py
   - Write comprehensive test cases
   - Include edge cases
   - Run and confirm failure

3. Implement Minimal Code (GREEN):
   - Write just enough to pass tests
   - No over-engineering
   - Focus on functionality

4. Refactor (REFACTOR):
   - Apply DRY principle
   - Improve readability
   - Add docstrings
   - Ensure tests still pass

5. Final Validation:
   - Run full test suite
   - Check coverage
   - Lint code

Create 3 commits (red, green, refactor).
```

## Example Output

```
🎯 TDD: Payment Processing

📝 Requirements analyzed: 5 test cases

🔴 RED Phase:
   Created: tests/test_payment.py
   - test_process_valid_payment
   - test_reject_insufficient_funds
   - test_handle_timeout
   - test_validate_card_number
   - test_refund_transaction
   ❌ 5 tests failing (expected)

🟢 GREEN Phase:
   Created: src/payment.py
   ✅ 5 tests passing

♻️ REFACTOR Phase:
   - Extracted CardValidator class
   - Added retry logic
   - Improved error messages
   ✅ 5 tests still passing

📊 Coverage: 94%
✅ 3 commits created
```
