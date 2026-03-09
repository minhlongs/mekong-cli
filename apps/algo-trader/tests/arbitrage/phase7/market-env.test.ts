/**
 * Tests: market-env.ts — RL environment state transitions and reward computation.
 */

import { MarketEnv } from '../../../src/arbitrage/phase7_aan/rlSpreadOptimizer/market-env';
import type { SpreadAction } from '../../../src/arbitrage/phase7_aan/rlSpreadOptimizer/market-env';

const neutralAction: SpreadAction = { spreadDeltaBps: 0, sizeMultiplier: 1.0 };
const widenAction: SpreadAction = { spreadDeltaBps: 3, sizeMultiplier: 0.5 };
const tightenAction: SpreadAction = { spreadDeltaBps: -2, sizeMultiplier: 1.5 };

describe('MarketEnv', () => {
  it('initialises with default state', () => {
    const env = new MarketEnv();
    const state = env.getState();
    expect(state.spread).toBeGreaterThan(0);
    expect(state.inventory).toBe(0);
    expect(state.midPrice).toBeGreaterThan(0);
  });

  it('reset returns clean initial state', () => {
    const env = new MarketEnv();
    env.step(widenAction);
    env.step(widenAction);
    const state = env.reset();
    expect(state.inventory).toBe(0);
    expect(env.getStepCount()).toBe(0);
  });

  it('step increments step count', () => {
    const env = new MarketEnv();
    env.step(neutralAction);
    env.step(neutralAction);
    expect(env.getStepCount()).toBe(2);
  });

  it('widening spread increases spread value', () => {
    const env = new MarketEnv({ targetSpreadBps: 5 });
    const before = env.getState().spread;
    env.step(widenAction);
    const after = env.getState().spread;
    expect(after).toBeGreaterThan(before);
  });

  it('tightening spread decreases spread value', () => {
    const env = new MarketEnv({ targetSpreadBps: 10 });
    env.step(tightenAction);
    const after = env.getState().spread;
    expect(after).toBeLessThan(10);
    expect(after).toBeGreaterThanOrEqual(1); // floor at 1
  });

  it('inventory stays within maxInventory bounds', () => {
    const env = new MarketEnv({ maxInventory: 0.5 });
    for (let i = 0; i < 50; i++) {
      env.step({ spreadDeltaBps: 0, sizeMultiplier: 3.0 });
    }
    const state = env.getState();
    expect(Math.abs(state.inventory)).toBeLessThanOrEqual(0.5);
  });

  it('step result includes reward, done flag and info', () => {
    const env = new MarketEnv();
    const result = env.step(neutralAction);
    expect(result).toHaveProperty('nextState');
    expect(result).toHaveProperty('reward');
    expect(result).toHaveProperty('done');
    expect(result.info).toHaveProperty('pnl');
    expect(result.info).toHaveProperty('inventoryPenalty');
    expect(result.info).toHaveProperty('fillProb');
  });

  it('done is true after maxEpisodeSteps', () => {
    const env = new MarketEnv({ maxEpisodeSteps: 3 });
    let done = false;
    for (let i = 0; i < 3; i++) {
      const r = env.step(neutralAction);
      done = r.done;
    }
    expect(done).toBe(true);
  });

  it('reward decreases with higher inventory penalty', () => {
    const lenient = new MarketEnv({ inventoryPenaltyFactor: 0.0 });
    const strict = new MarketEnv({ inventoryPenaltyFactor: 10.0 });
    // Force inventory via seed-controlled random is not feasible,
    // so we compare expected penalty behavior over many steps
    let sumLenient = 0;
    let sumStrict = 0;
    for (let i = 0; i < 20; i++) {
      sumLenient += lenient.step(widenAction).reward;
      sumStrict += strict.step(widenAction).reward;
    }
    expect(sumLenient).toBeGreaterThanOrEqual(sumStrict);
  });
});
