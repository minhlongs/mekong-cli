import { IStrategy, SignalType } from '../interfaces/IStrategy';
import { IDataProvider } from '../interfaces/IDataProvider';
import { IExchange } from '../interfaces/IExchange';
import { RiskManager } from './RiskManager';
import { OrderManager } from './OrderManager';
import { ICandle } from '../interfaces/ICandle';

export interface BotConfig {
  symbol: string;
  riskPercentage: number;
  pollInterval: number; // ms
}

export class BotEngine {
  private strategy: IStrategy;
  private dataProvider: IDataProvider;
  private exchange: IExchange;
  private orderManager: OrderManager;
  private config: BotConfig;
  private isRunning = false;
  private openPosition = false; // Simplified state tracking

  constructor(
    strategy: IStrategy,
    dataProvider: IDataProvider,
    exchange: IExchange,
    config: BotConfig
  ) {
    this.strategy = strategy;
    this.dataProvider = dataProvider;
    this.exchange = exchange;
    this.orderManager = new OrderManager();
    this.config = config;
  }

  async start() {
    console.log('Starting Bot Engine...');
    await this.exchange.connect();
    await this.dataProvider.init();

    // Warm up strategy with history if possible, or just start listening
    // For now, let's assume we subscribe to live data
    this.dataProvider.subscribe(this.onCandle.bind(this));
    await this.dataProvider.start();

    this.isRunning = true;
    console.log('Bot Engine Running.');
  }

  async stop() {
    console.log('Stopping Bot Engine...');
    await this.dataProvider.stop();
    this.isRunning = false;
  }

  private async onCandle(candle: ICandle) {
    if (!this.isRunning) return;

    try {
      const signal = await this.strategy.onCandle(candle);

      if (signal) {
        console.log(`[SIGNAL] ${signal.type} @ ${signal.price} (${JSON.stringify(signal.metadata)})`);

        if (signal.type === SignalType.BUY && !this.openPosition) {
          await this.executeBuy(signal.price);
        } else if (signal.type === SignalType.SELL && this.openPosition) {
          await this.executeSell(signal.price);
        }
      }
    } catch (error) {
      console.error('Error in onCandle processing:', error);
    }
  }

  private async executeBuy(currentPrice: number) {
    // 1. Check Balance
    // Assuming pair like BTC/USDT, we need USDT balance
    const quoteCurrency = this.config.symbol.split('/')[1];
    const balances = await this.exchange.fetchBalance();
    const balance = balances[quoteCurrency]?.free || 0;

    if (balance === 0) {
      console.warn(`Insufficient ${quoteCurrency} balance.`);
      return;
    }

    // 2. Risk Management
    const amount = RiskManager.calculatePositionSize(balance, this.config.riskPercentage, currentPrice);

    console.log(`Executing BUY for ${amount} ${this.config.symbol}...`);

    // 3. Execute Order
    // In real bot, we would handle errors, partial fills, etc.
    // For demo/bootstrap, we assume success or mock
    try {
      const order = await this.exchange.createMarketOrder(this.config.symbol, 'buy', amount);
      this.orderManager.addOrder(order);
      this.openPosition = true;
    } catch (e) {
      console.error('Buy order failed:', e);
    }
  }

  private async executeSell(currentPrice: number) {
    // 1. Get position size
    // For simplicity, we sell everything of the base currency
    const baseCurrency = this.config.symbol.split('/')[0];
    const balances = await this.exchange.fetchBalance();
    const amount = balances[baseCurrency]?.free || 0;

    if (amount === 0) {
      console.warn(`No ${baseCurrency} to sell.`);
      return;
    }

    console.log(`Executing SELL for ${amount} ${this.config.symbol}...`);

    try {
      const order = await this.exchange.createMarketOrder(this.config.symbol, 'sell', amount);
      this.orderManager.addOrder(order);
      this.openPosition = false;
    } catch (e) {
      console.error('Sell order failed:', e);
    }
  }
}
