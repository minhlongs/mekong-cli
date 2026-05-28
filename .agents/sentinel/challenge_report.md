## Challenge Summary

**Overall risk assessment**: LOW

The UI/UX and testing structure in the polished codebase is robust. The introduction of minimum touch targets, proper focus indicator outlines, and dark mode classes aligns with best practices. However, we have identified minor edge cases and architectural assumptions that could cause failure under specific stress scenarios.

---

## Challenges

### [Medium] Challenge 1: IP Rate-Limiting Collisions for Shared Client Networks
- **Assumption challenged**: The rate limiter assumes that each client operates from a unique public IP address (`cf-connecting-ip` or the first entry in `x-forwarded-for`).
- **Attack scenario**: Multiple CRM users or automated partners working from a shared corporate office or VPN will share the same public IP address. Under high concurrent usage (e.g., bulk importing leads or rapid board actions), their collective requests may trigger the `REQUESTS_PER_MINUTE = 10000` limit, locking out innocent users.
- **Blast radius**: Temporary lockout (429 Too Many Requests) for users on shared IPs.
- **Mitigation**: Update the rate limit key structure to include the authenticated user/session ID (e.g., `rl:{ip}:{userId}:{minute}`) once user identification is verified.

### [Low] Challenge 2: Graceful Degradation of AI Scoring Panel on Network Errors
- **Assumption challenged**: The AI predictive scoring API endpoint is highly available and responds quickly within the client lifecycle.
- **Attack scenario**: During periods of high LLM backend latency or server errors, the `getPredictiveLeadScoreAction` call on the Leads page could hang or reject. 
- **Blast radius**: The page displays a loading spinner indefinately if the request hangs, or defaults to "Chưa có thông tin chấm điểm AI" (No AI score info) if it fails. The spinner does not freeze the browser, but it may cause visual confusion.
- **Mitigation**: Implement a timeout (e.g., 5 seconds) on the client fetch action so it automatically stops the spinner and falls back to a clean placeholder.

---

## Stress Test Results

- **Shared Public IP Simulation** → The rate limit threshold of 10,000 requests per minute is sufficiently large that standard manual/E2E test runs do not trigger it, but script-based concurrent pipelines could.
- **Zero-width Viewport Scaling (320px to 375px)** → Simulated under 375px width. Main navigation hides automatically into the mobile menu drawer (`SheetTrigger`), and tables/boards display clean horizontal scrollbars without breaking page layout.

---

## Unchallenged Areas

- **OAuth 2.0 Auth State Handling** — Out of scope. We focused primarily on the UI/UX rendering layers, accessibility properties, and the RAG/E2E test execution.
