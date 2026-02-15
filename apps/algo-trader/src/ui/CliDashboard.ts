import * as chalk from 'chalk';
import { IOrder } from '../interfaces/IExchange';

export class CliDashboard {
  private lastPrice: number = 0;
  private lastSignal: string = 'NONE';
  private openPositions: number = 0;
  private balance: number = 0;

  updatePrice(price: number) {
    this.lastPrice = price;
    this.render();
  }

  updateSignal(signal: string) {
    this.lastSignal = signal;
    this.render();
  }

  updateBalance(balance: number) {
    this.balance = balance;
    this.render();
  }

  updatePositions(count: number) {
    this.openPositions = count;
    this.render();
  }

  render() {
    console.clear();
    console.log(chalk.bold.blue('=== ALGO TRADER DASHBOARD ==='));
    console.log(`Time: ${new Date().toISOString()}`);
    console.log('-----------------------------');
    console.log(`Current Price:  ${chalk.green(this.lastPrice)}`);
    console.log(`Last Signal:    ${this.getColorForSignal(this.lastSignal)(this.lastSignal)}`);
    console.log(`Balance:        ${this.balance.toFixed(2)}`);
    console.log(`Open Positions: ${this.openPositions}`);
    console.log('-----------------------------');
  }

  private getColorForSignal(signal: string) {
    switch (signal) {
      case 'BUY': return chalk.green;
      case 'SELL': return chalk.red;
      default: return chalk.grey;
    }
  }
}
