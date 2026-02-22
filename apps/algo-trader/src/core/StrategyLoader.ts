import { IStrategy } from '../interfaces/IStrategy';
import { RsiSmaStrategy } from '../strategies/RsiSmaStrategy';
import { RsiCrossoverStrategy } from '../strategies/RsiCrossoverStrategy';
import { CrossExchangeArbitrage } from '../strategies/CrossExchangeArbitrage';
import { TriangularArbitrage } from '../strategies/TriangularArbitrage';
import { StatisticalArbitrage } from '../strategies/StatisticalArbitrage';

export class StrategyLoader {
  private static strategies: Map<string, new () => IStrategy> = new Map<string, new () => IStrategy>([
    ['RsiSma', RsiSmaStrategy],
    ['RsiCrossover', RsiCrossoverStrategy],
    ['CrossExchange', CrossExchangeArbitrage],
    ['Triangular', TriangularArbitrage],
    ['Statistical', StatisticalArbitrage],
  ]);

  static register(name: string, strategyClass: new () => IStrategy) {
    this.strategies.set(name, strategyClass);
  }

  static load(name: string): IStrategy {
    const StrategyClass = this.strategies.get(name);
    if (!StrategyClass) {
      throw new Error(`Strategy ${name} not found. Available: ${Array.from(this.strategies.keys()).join(', ')}`);
    }

    return new StrategyClass();
  }
}
