// Ambient module declarations for packages without type definitions

declare module 'axios' {
  const axios: unknown;
  export default axios;
  export const get: unknown;
  export const post: unknown;
  export const create: unknown;
}

declare module 'ethers' {
  export class Wallet {
    constructor(privateKey: string, provider?: unknown);
    address: string;
    [key: string]: unknown;
  }
  export class providers {
    static JsonRpcProvider: unknown;
  }
  export const utils: unknown;
  export const BigNumber: unknown;
}

declare module '@polymarket/clob-client' {
  export class ClobClient {
    constructor(...args: unknown[]);
    [key: string]: unknown;
    getBalanceAllowance(params: unknown): Promise<unknown>;
    createOrDeriveApiKey(): Promise<unknown>;
    cancelAll(): Promise<unknown>;
    postHeartbeat(id: string): Promise<unknown>;
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
    [key: string]: unknown;
  }

  export interface UserMarketOrder {
    tokenID: string;
    side: Side;
    amount?: number;
    size?: number;
    [key: string]: unknown;
  }

  export interface OrderResponse {
    success: boolean;
    orderId?: string;
    [key: string]: unknown;
  }

  export interface CreateOrderOptions {
    tickSize?: string;
    negRisk?: boolean;
    [key: string]: unknown;
  }

  export interface OpenOrder {
    id: string;
    token_id: string;
    price: number;
    size: number;
    side: Side;
    [key: string]: unknown;
  }

  export interface Trade {
    id: string;
    price: number;
    size: number;
    side: Side;
    [key: string]: unknown;
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
