# Algo-Trader Knowledge Synthesis

**Date:** 2026-02-23
**Context:** Synthesis of learnings from recent testing and debugging missions covering `BollingerBandStrategy`, `MacdCrossoverStrategy`, and `indicators` modules.

---

## 1. Jest Mocking for Static Methods (Algorithmic Indicators)

**GOTCHA:**
When testing trading strategies that rely on deterministic mathematical indicators (like MACD or Bollinger Bands), you often need to simulate extreme edge cases (e.g., indicator utility functions returning empty arrays due to bad data or initialization errors).

**LEARNING:**
You can dynamically mock static methods of imported utility classes within a specific Jest test block, ensuring that you isolate the edge case without breaking the pure implementation for subsequent tests.

**Actionable Pattern:**
```typescript
// Dynamically require and mock the static method
const { Indicators } = require('../analysis/indicators');
const originalMacd = Indicators.macd;
Indicators.macd = jest.fn().mockReturnValue([]);

// Execute the test scenario
const result = await strategy.onCandle(candle);
expect(result).toBeNull();

// CRITICAL: Always restore the original method
Indicators.macd = originalMacd;
```

## 2. Time-Series Buffer Limits (Memory Management)

**GOTCHA:**
Trading bots running 24/7 will process thousands of tick/candle events. If a strategy indiscriminately appends every new candle to its local state (`this.candles.push(candle)`), it will rapidly consume RAM, leading to an eventual Out-Of-Memory (OOM) crash.

**LEARNING:**
Implement a strict FIFO buffer limit inside the `onCandle` handler to maintain only the rolling window of history required by the indicators.

**Actionable Pattern:**
```typescript
this.candles.push(candle);

// Trim the buffer (e.g., keep only the last 200 or 300 candles)
if (this.candles.length > 200) {
  this.candles.shift();
}
```
*Rule of Thumb:* The buffer size limit MUST be strictly greater than the maximum period required by any indicator logic (e.g., MACD slow period 26 + signal period 9 requires a minimum of 35 candles, so a buffer of 300 is safe).

## 3. Edge Case Handling & Strategy Initialization

**GOTCHA:**
Strategies crash or emit false signals if they calculate indicators before accumulating sufficient historical data. Additionally, cross-over indicators (like MACD) require the *previous* state to determine if a line has "crossed" the signal line.

**LEARNING:**
1. **Min Required Guard:** Always check `candles.length < minRequired` before processing calculations.
2. **Warm-up Phase:** Initialize and "warm up" past indicator states (like `this.prevMacd`) inside the `init(history)` method so that crossover logic functions correctly on the very first live candle.
3. **Undefined Checks:** Indicator libraries often pad the beginning of arrays with `undefined` values. Explicitly verify properties exist before comparing them.

**Actionable Pattern:**
```typescript
// 1. Guard against insufficient data
const minRequired = this.slowPeriod + this.signalPeriod + 1;
if (this.candles.length < minRequired) return null;

// 2. Strict Crossover Comparison (checking for undefined)
if (prev.MACD !== undefined && prev.signal !== undefined &&
    current.MACD !== undefined && current.signal !== undefined &&
    prev.MACD <= prev.signal && current.MACD > current.signal) {
  // Trigger Bullish Crossover
}
```

## 4. Structured Signals & Type Safety

**GOTCHA:**
Returning bare `BUY` or `SELL` signals makes it incredibly difficult to debug *why* a bot executed a trade, especially when a single strategy might have multiple entry/exit conditions. Furthermore, missing interface definitions will cause build failures during test execution (e.g., `TS2339: Property 'tag' does not exist on type 'ISignal'`).

**LEARNING:**
- Include descriptive tags (e.g., `tag: 'macd_bullish_crossover'`, `tag: 'bb_lower_rsi_oversold'`) inside the generated signal.
- Attach indicator snapshots via a `metadata` payload to maintain an audit trail of the mathematical state at the exact moment the signal was emitted.
- **Action Item:** Ensure `ISignal` interface in `src/interfaces/IStrategy.ts` is updated to include `tag?: string;` to satisfy TypeScript checks during CI pipelines.