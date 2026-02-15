import { IDataProvider } from '../interfaces/IDataProvider';
import { ICandle } from '../interfaces/ICandle';

export class MockDataProvider implements IDataProvider {
  private subscribers: ((candle: ICandle) => void)[] = [];
  private interval: NodeJS.Timeout | null = null;
  private isRunning = false;

  // Mock data state
  private currentPrice = 100;
  private trend = 1; // 1 for up, -1 for down
  private volatility = 0.5;

  async init(): Promise<void> {
    console.log('Mock Data Provider Initialized');
  }

  subscribe(callback: (candle: ICandle) => void): void {
    this.subscribers.push(callback);
  }

  async getHistory(limit: number): Promise<ICandle[]> {
    const history: ICandle[] = [];
    let price = this.currentPrice;
    const now = Date.now();
    const minute = 60 * 1000;

    for (let i = limit; i > 0; i--) {
      const candle = this.generateCandle(now - i * minute, price);
      price = candle.close;
      history.push(candle);
    }

    this.currentPrice = price;
    return history;
  }

  async start(): Promise<void> {
    if (this.isRunning) return;
    this.isRunning = true;
    console.log('Mock Data Feed Started');

    this.interval = setInterval(() => {
      const candle = this.generateCandle(Date.now(), this.currentPrice);
      this.currentPrice = candle.close;
      this.notifySubscribers(candle);
    }, 1000); // Fast forward: 1 second = 1 candle for testing
  }

  async stop(): Promise<void> {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.isRunning = false;
    console.log('Mock Data Feed Stopped');
  }

  private notifySubscribers(candle: ICandle): void {
    this.subscribers.forEach(sub => sub(candle));
  }

  private generateCandle(timestamp: number, startPrice: number): ICandle {
    // Random walk with trend
    if (Math.random() > 0.95) this.trend *= -1; // Change trend occasionally

    const change = (Math.random() - 0.5 + (this.trend * 0.1)) * this.volatility;
    const close = startPrice * (1 + change / 100);
    const high = Math.max(startPrice, close) * (1 + Math.random() * 0.002);
    const low = Math.min(startPrice, close) * (1 - Math.random() * 0.002);
    const volume = Math.floor(Math.random() * 1000) + 100;

    return {
      timestamp,
      open: startPrice,
      high,
      low,
      close,
      volume
    };
  }
}
