// Ambient module declarations for packages without type definitions

declare module 'axios' {
  const axios: any;
  export default axios;
  export const get: any;
  export const post: any;
  export const create: any;
}

declare module 'ethers' {
  export class Wallet {
    constructor(privateKey: string, provider?: any);
    address: string;
    [key: string]: any;
  }
  export class providers {
    static JsonRpcProvider: any;
  }
  export const utils: any;
  export const BigNumber: any;
}

declare module '@polymarket/clob-client' {
  export class ClobClient {
    constructor(...args: any[]);
    [key: string]: any;
    getBalanceAllowance(params: any): Promise<any>;
    createOrDeriveApiKey(): Promise<any>;
    cancelAll(): Promise<any>;
    postHeartbeat(id: string): Promise<any>;
  }

  export interface ApiKeyCreds {
    key: string;
    secret: string;
    passphrase: string;
  }

  export interface UserOrder {
    tokenID: string;
    price: number;
    side: Side;
    size: number;
    [key: string]: any;
  }

  export interface UserMarketOrder {
    tokenID: string;
    side: Side;
    amount?: number;
    size?: number;
    [key: string]: any;
  }

  export interface OrderResponse {
    success: boolean;
    orderId?: string;
    [key: string]: any;
  }

  export interface CreateOrderOptions {
    tickSize?: string;
    negRisk?: boolean;
    [key: string]: any;
  }

  export interface OpenOrder {
    id: string;
    token_id: string;
    price: number;
    size: number;
    side: Side;
    [key: string]: any;
  }

  export interface Trade {
    id: string;
    price: number;
    size: number;
    side: Side;
    [key: string]: any;
  }

  export enum Side {
    BUY = 'BUY',
    SELL = 'SELL',
  }

  export enum OrderType {
    GTC = 'GTC',
    GTD = 'GTD',
    FOK = 'FOK',
    FAK = 'FAK',
  }

  export const GTC: string;
  export const GTD: string;
  export const FOK: string;
  export const FAK: string;
}
