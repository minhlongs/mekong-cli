import { IOrder } from '../interfaces/IExchange';

export class OrderManager {
  private orders: IOrder[] = [];

  addOrder(order: IOrder) {
    this.orders.push(order);
    console.log(`[OrderManager] Order added: ${order.side.toUpperCase()} ${order.amount} @ ${order.price}`);
  }

  getOrders(): IOrder[] {
    return this.orders;
  }

  getOpenOrders(): IOrder[] {
    return this.orders.filter(o => o.status === 'open');
  }

  getLastOrder(): IOrder | undefined {
    return this.orders[this.orders.length - 1];
  }
}
