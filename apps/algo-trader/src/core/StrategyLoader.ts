import { IStrategy } from '../interfaces/IStrategy';
import { RsiSmaStrategy } from '../strategies/RsiSmaStrategy';
import { RsiCrossoverStrategy } from '../strategies/RsiCrossoverStrategy';
import { CrossExchangeArbitrage } from '../strategies/CrossExchangeArbitrage';
import { TriangularArbitrage } from '../strategies/TriangularArbitrage';
import { StatisticalArbitrage } from '../strategies/StatisticalArbitrage';

export class StrategyLoader {
  private static strategies: Map<string, new () => IStrategy> = new Map();

  static register(name: string, strategyClass: new () => IStrategy) {
    this.strategies.set(name, strategyClass);
  }

  static load(name: string): IStrategy {
    // Register default strategies
    this.register('RsiSma', RsiSmaStrategy);
    this.register('RsiCrossover', RsiCrossoverStrategy);
    this.register('CrossExchange', CrossExchangeArbitrage);
    this.register('Triangular', TriangularArbitrage);
    this.register('Statistical', StatisticalArbitrage);

    const StrategyClass = this.strategies.get(name);
    if (!StrategyClass) {
      throw new Error(`Strategy ${name} not found. Available: ${Array.from(this.strategies.keys()).join(', ')}`);
    }

    return new StrategyClass();
  }
}
