# Phase 2: NLP Commander Robustness

## Context Links

- Source: `/Users/macbookprom1/mekong-cli/src/core/nlp_commander.py` (333 lines)
- Depends on: Phase 1 (improved LLM client)

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 1h

Better error reporting, parse-level retry with simplified prompt, configurable memory context cap, and LLM call timing.

## Key Insights

- `_fallback_parse()` always sets `parse_error = "Gemini returned empty -> Fallback used"` (line 288) -- no info about WHY
- No retry at `parse()` level -- single LLM call, then fallback
- Memory context cap hardcoded to 1000 chars (line 158) -- should be configurable
- No timing metrics on LLM calls

## Requirements

- `parse_error` includes provider mode and error details
- One retry with simplified prompt before falling to regex fallback
- `MEMORY_CONTEXT_MAX` class constant (default 1000)
- Log LLM call duration

## Architecture

```
parse(message)
  --> LLM call #1 (full prompt + memory context)
  --> if empty/error: LLM call #2 (simplified prompt, no memory context)
  --> if still empty: _fallback_parse() with detailed error
```

## Related Code Files

- **Modify**: `src/core/nlp_commander.py`

## Implementation Steps

1. Add `import time` at top of file (after `import logging`, line 9)

2. Add class constant to `NLPCommander` (after line 129):
   ```python
   MEMORY_CONTEXT_MAX = 1000  # chars
   ```

3. In `parse()`, replace the hardcoded `[:1000]` at line 158 with `[:self.MEMORY_CONTEXT_MAX]`

4. Wrap the LLM call (lines 167-175) with timing:
   ```python
   call_start = time.time()
   response = client.chat(...)
   call_duration = time.time() - call_start
   logger.info(f"NLP LLM call took {call_duration:.2f}s (mode={client.mode})")
   ```

5. After empty response check (lines 178-182), add retry with simplified prompt instead of immediate fallback:
   ```python
   if not content or not content.strip():
       logger.warning(f"NLP: empty response from {client.mode}. Retrying with simplified prompt...")
       simplified = f"Parse this into JSON with keys: intent, project, summary, cc_cli_prompt, claudekit_commands, priority, needs_confirmation.\n\nMessage: {message}"
       retry_response = client.chat(
           messages=[{"role": "user", "content": simplified}],
           temperature=0.2,
           max_tokens=1024,
           json_mode=True,
       )
       content = retry_response.content
       if not content or not content.strip():
           logger.warning("NLP: retry also empty.")
           return self._fallback_parse(message, error_detail=f"provider={client.mode}, both attempts empty")
       content = content.strip()
   ```

6. Update `_fallback_parse()` signature to accept `error_detail` param:
   ```python
   def _fallback_parse(self, message: str, error_detail: str = "") -> StructuredTask:
   ```

7. Update `parse_error` in `_fallback_parse()` return (line 288):
   ```python
   parse_error=f"LLM fallback: {error_detail}" if error_detail else "Gemini returned empty -> Fallback used",
   ```

8. Update the `except json.JSONDecodeError` block (line 221-223) to pass detail:
   ```python
   return self._fallback_parse(message, error_detail=f"JSON decode error: {e}")
   ```

9. Update the general `except Exception` block (line 224-226):
   ```python
   return self._fallback_parse(message, error_detail=f"provider={client.mode}, error={e}")
   ```

## Todo List

- [ ] Add `import time`
- [ ] Add `MEMORY_CONTEXT_MAX` class constant
- [ ] Use class constant for context truncation
- [ ] Add LLM call timing/logging
- [ ] Add retry with simplified prompt on empty response
- [ ] Update `_fallback_parse()` to accept `error_detail`
- [ ] Improve `parse_error` messages in all error paths
- [ ] Run `python3 -m pytest tests/ -v` -- all tests pass

## Success Criteria

- When Gemini returns empty, a simplified retry is attempted before regex fallback
- `parse_error` includes provider name and specific error
- LLM call duration logged
- Memory context cap is configurable via class constant

## Risk Assessment

- **Extra LLM call**: Retry doubles API usage on failure. Acceptable -- only fires on empty response
- **Simplified prompt quality**: May produce less accurate results than full prompt. Acceptable -- better than regex fallback

## Security Considerations

- No new secrets or auth changes

## Next Steps

- Phase 3 uses the improved LLM client for AGI loop assessment
