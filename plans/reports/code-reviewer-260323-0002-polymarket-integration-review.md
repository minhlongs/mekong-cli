# Code Review: Polymarket Integration for algo-trader

**Reviewer:** code-reviewer | **Date:** 2026-03-23 | **Score: 7/10**

---

## Scope

- **Files:** 8 files, 1454 LOC total
- **Focus:** New Polymarket prediction market integration (WS feed, EIP-712 signer, CLOB adapter, binary arb detection/execution, settlement listener, LLM probability calibrator, updated types)

## Overall Assessment

Well-structured integration that follows existing algo-trader patterns (extends BaseWebSocketClient, reuses ArbitrageOpportunity types). Code is readable, modular, and demonstrates solid trading safety defaults (dryRun=true, fractional Kelly). However, there are **critical security issues** with secret handling and several trading logic concerns that need addressing before any live usage.

---

## CRITICAL Issues

### C1. Private Key Exposed as Public Property (polymarket-signer.ts:74)

```typescript
readonly privateKey: string;  // PUBLIC readonly — accessible from any consumer
```

**Impact:** Any code with a reference to the signer can read `signer.privateKey` and log/exfiltrate it. This is a wallet-draining vulnerability if the key controls real funds.

**Fix:** Change to `private readonly privateKey: string;`. It is already declared `readonly` but the access modifier is missing `private`.

### C2. API Secret Exposed as Public Property (polymarket-adapter.ts:78)

```typescript
readonly apiSecret: string;  // PUBLIC — same issue
```

The comment says "Used in HMAC-SHA256 signature" but the field is readable externally. Any caller can do `adapter.apiSecret`.

**Fix:** Change to `private readonly apiSecret: string;`.

### C3. Stub Signing Produces Invalid Orders (polymarket-signer.ts:160-163)

The `_stubSign` returns `0x000...0` and `_stubGetAddress` returns the zero address. If `dryRun=false` is accidentally set, these stubs would submit malformed orders to the CLOB API -- potentially losing funds or triggering bans.

**Fix:** Add a runtime guard in `signOrder()`:

```typescript
if (this._isStub) {
  throw new Error('Cannot sign real orders: ethers.js not yet integrated');
}
```

Or check at adapter level before calling `placeOrder`.

### C4. Empty HMAC Signature Sent to Authenticated Endpoints (polymarket-adapter.ts:182,216)

`_stubSignature` returns `''`. If the API key is set but HMAC is blank, the request will either fail silently or worse, some endpoints may accept unauthenticated requests.

**Fix:** Throw if `apiKey` is set but HMAC is not implemented. Never send empty auth headers.

---

## HIGH Priority

### H1. No Input Validation on tokenId/conditionId (multiple files)

`subscribe()`, `getMarketInfo()`, `getOrderBook()`, `fetchResolution()` pass user-provided strings directly into URLs:

```typescript
`/markets/${conditionId}`  // polymarket-adapter.ts:128
`/book?token_id=${tokenId}`  // polymarket-adapter.ts:136
`${this.apiBase}/markets/${conditionId}`  // settlement-listener.ts:125
```

No validation that these are valid hex strings. Malformed IDs could cause unexpected API errors or in theory URL manipulation.

**Fix:** Validate conditionId matches `^0x[a-fA-F0-9]+$` pattern before use. Use `encodeURIComponent()` for query params.

### H2. Kelly Criterion Uses `maxPositionSize` as Bankroll (binary-arbitrage-executor.ts:53)

```typescript
const bankroll = this.config.maxPositionSize;
```

`maxPositionSize` is a per-trade cap, not the total bankroll. Kelly formula requires actual total capital to size correctly. Using max position size means Kelly fractions are computed on the wrong base, leading to oversized positions when `maxPositionSize` is large relative to true capital.

**Fix:** Add a separate `bankroll` field to `BinaryExecutorConfig`.

### H3. `placeOrders` is Still a Stub (binary-arbitrage-executor.ts:136-148)

When `dryRun=false`, `placeOrders()` returns simulated legs with random txHash instead of calling the PolymarketAdapter. This means live execution silently does nothing real and reports fake profits.

**Fix:** Either wire to PolymarketAdapter or throw `Error('Live execution not yet wired')`.

### H4. Drawdown Check Uses PnL vs maxPositionSize, Not vs Actual Bankroll (binary-arbitrage-executor.ts:111)

```typescript
const drawdownFraction = Math.abs(currentPnL) / this.config.maxPositionSize;
```

Should be divided by actual bankroll, not maxPositionSize. If bankroll = $100k but maxPositionSize = $1k, a $200 loss (20% of $1k) triggers the halt even though it's only 0.2% of bankroll.

### H5. File Size Violations

| File | Lines | Over Limit |
|------|-------|------------|
| polymarket-ws-feed.ts | 218 | +18 |
| polymarket-adapter.ts | 218 | +18 |
| probability-calibrator.ts | 202 | +2 |

Per project rules, files must be under 200 lines. The WS feed can extract interfaces to a separate `polymarket-ws-types.ts`. The adapter can extract response interfaces similarly.

---

## MEDIUM Priority

### M1. Nonce Generation Uses Math.random() (polymarket-signer.ts:154)

```typescript
return Math.floor(Math.random() * Number.MAX_SAFE_INTEGER).toString();
```

`Math.random()` is not cryptographically secure. For order nonces that prevent replay attacks, use `crypto.getRandomValues()` or `crypto.randomUUID()`.

### M2. `fairYes = 0.5` Hardcoded Baseline (binary-opportunity-detector.ts:78)

The comment says "LLM calibration overrides this" but there is no mechanism to pass calibrated probabilities into the detector. The detector always assumes 50/50 for single-side edge detection, making it useless for markets with non-50% probabilities.

**Fix:** Accept optional `calibratedProbability` in `calculateEdge()` or `evaluateMarket()`.

### M3. Settlement Listener Does Not Handle HTTP Errors Gracefully (settlement-listener.ts:125-126)

```typescript
const response = await fetch(`${this.apiBase}/markets/${conditionId}`);
if (!response.ok) return null;
```

Silently swallowing all HTTP errors (rate limits, 500s, auth failures) makes debugging production issues very difficult. At minimum emit an error event with the status code.

### M4. Unused `assets` Variable in subscribe() (polymarket-ws-feed.ts:94,102)

```typescript
const assets = marketIds.map((id) => ({ asset_id: id }));  // line 94
// ...
this.sendMessage({ ...message, assets });  // line 102
```

The `message` already has `assets_ids` array. Spreading both `assets` (array of objects) and `assets_ids` (array of strings) may confuse the Polymarket WS API. Check the API docs for the correct shape.

### M5. No Request Timeout on fetch() Calls (polymarket-adapter.ts, settlement-listener.ts, probability-calibrator.ts)

All `fetch()` calls lack `AbortController` timeouts. A hanging HTTP connection blocks the event loop indefinitely. Critical for a trading system.

**Fix:** Add `AbortSignal.timeout(10000)` or similar.

---

## LOW Priority

### L1. `PolymarketOrderBook` Duplicate Name

`PolymarketOrderBook` is defined in both `polymarket-ws-feed.ts:42` and `polymarket-adapter.ts:39` with different shapes. Will cause confusion when both are imported.

### L2. Missing `destroyed` Guard on SettlementListener

After `destroy()`, calling `watchMarket()` will re-create the poll timer. Add a `destroyed` flag.

### L3. Confidence Clamping Formula (binary-opportunity-detector.ts:120)

```typescript
confidence: Math.min(95, 50 + edge * 500)
```

A 3% edge produces 65% confidence, 9% edge = 95% (capped). This is an arbitrary linear mapping with no statistical basis. Consider documenting this is a heuristic, or use calibrated probabilities.

---

## Positive Observations

- Extends `BaseWebSocketClient` correctly; heartbeat and reconnect logic inherited
- `BinaryArbitrageOpportunity` properly extends `ArbitrageOpportunity` type
- `dryRun: true` as default -- safe production default
- Fractional Kelly (0.25) with position size cap -- conservative sizing
- Semaphore for LLM concurrency -- prevents OOM on local GPU
- LLM response parsing with graceful fallback on malformed JSON
- Clean separation: detector (signal) vs executor (action) vs listener (settlement)
- Good use of `Promise.allSettled` in settlement checker
- Execution audit log with read-only access

---

## Recommended Actions (Priority Order)

1. **[CRITICAL]** Make `privateKey` and `apiSecret` private properties
2. **[CRITICAL]** Add runtime guard against stub signing in live mode
3. **[CRITICAL]** Throw on empty HMAC signature when API key is configured
4. **[HIGH]** Validate tokenId/conditionId inputs, use encodeURIComponent
5. **[HIGH]** Add separate `bankroll` config for Kelly sizing
6. **[HIGH]** Wire `placeOrders` to PolymarketAdapter or throw on live mode
7. **[HIGH]** Split oversized files (extract interfaces to separate type files)
8. **[MEDIUM]** Use crypto-safe nonce generation
9. **[MEDIUM]** Add fetch timeouts via AbortController
10. **[MEDIUM]** Emit error events in settlement listener for HTTP failures

---

## Metrics

| Metric | Value |
|--------|-------|
| Files Reviewed | 8 |
| Total LOC | 1454 |
| Files Over 200 Lines | 3 |
| Critical Issues | 4 |
| High Issues | 5 |
| Medium Issues | 5 |
| Low Issues | 3 |
| TODOs in Code | 7 (all in signer/adapter stubs) |

## Verdict: **REQUEST_CHANGES**

The 4 critical security issues (private key exposure, API secret exposure, stub signing in live path, empty HMAC) must be fixed before merge. The stub TODOs are acceptable for Phase 1 only if live execution is gated behind a runtime check that throws.

---

## Unresolved Questions

1. Is ethers.js planned as a dependency, or should we use viem/noble for lighter bundle?
2. Should the detector accept calibrated probabilities from the LLM calibrator, or is the integration planned at a higher orchestration layer?
3. What is the actual HMAC signature format for the Polymarket CLOB API v2 -- the current TODO references the old format?
