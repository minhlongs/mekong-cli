export interface Product {
  id: string;
  name: string;
  description: string;
  basePriceUsd: number;
  tier: "starter" | "pro" | "enterprise";
  features: string[];
  active: boolean;
}

export interface PromoCode {
  code: string;
  discountPercent: number;
  expiresAt: Date;
  maxUses: number;
  usedCount: number;
}

export interface PricingContext {
  quantity?: number;
  promoCode?: string;
}

export interface ProductFilter {
  tier?: Product["tier"];
  active?: boolean;
}

const DEFAULT_PRODUCTS: Product[] = [
  {
    id: "openclaw-starter",
    name: "OpenClaw Starter",
    description: "Perfect for small teams and solo founders",
    basePriceUsd: 49,
    tier: "starter",
    features: ["200 MCU/mo", "5 agents", "Community support", "CF deploy"],
    active: true,
  },
  {
    id: "openclaw-pro",
    name: "OpenClaw Pro",
    description: "For growing businesses needing more power",
    basePriceUsd: 149,
    tier: "pro",
    features: ["1000 MCU/mo", "20 agents", "Priority support", "Custom domain"],
    active: true,
  },
  {
    id: "openclaw-enterprise",
    name: "OpenClaw Enterprise",
    description: "Unlimited scale for serious operators",
    basePriceUsd: 499,
    tier: "enterprise",
    features: ["Unlimited MCU", "Unlimited agents", "24/7 support", "SLA"],
    active: true,
  },
];

export class ProductCatalog {
  private products: Map<string, Product> = new Map();
  private promos: Map<string, PromoCode> = new Map();

  constructor() {
    for (const p of DEFAULT_PRODUCTS) {
      this.products.set(p.id, p);
    }
  }

  addProduct(product: Product): void {
    this.products.set(product.id, product);
  }

  getProduct(id: string): Product | undefined {
    return this.products.get(id);
  }

  listProducts(filter?: ProductFilter): Product[] {
    let results = Array.from(this.products.values());
    if (filter?.tier !== undefined) {
      results = results.filter((p) => p.tier === filter.tier);
    }
    if (filter?.active !== undefined) {
      results = results.filter((p) => p.active === filter.active);
    }
    return results;
  }

  calculatePrice(productId: string, context?: PricingContext): number {
    const product = this.products.get(productId);
    if (!product) throw new Error(`Product not found: ${productId}`);

    let price = product.basePriceUsd;
    const qty = context?.quantity ?? 1;

    // Quantity discount: 5% per unit over 1, max 30%
    const qtyDiscount = Math.min((qty - 1) * 0.05, 0.3);
    price = price * qty * (1 - qtyDiscount);

    // Promo discount
    if (context?.promoCode) {
      const promo = this.promos.get(context.promoCode.toUpperCase());
      if (promo && this.isPromoValid(promo)) {
        price = price * (1 - promo.discountPercent / 100);
      }
    }

    return Math.round(price * 100) / 100;
  }

  addPromo(promo: PromoCode): void {
    this.promos.set(promo.code.toUpperCase(), promo);
  }

  applyPromo(productId: string, code: string): { price: number; discount: number } {
    const product = this.products.get(productId);
    if (!product) throw new Error(`Product not found: ${productId}`);

    const promo = this.promos.get(code.toUpperCase());
    if (!promo || !this.isPromoValid(promo)) {
      return { price: product.basePriceUsd, discount: 0 };
    }

    const discount = Math.round(product.basePriceUsd * (promo.discountPercent / 100) * 100) / 100;
    const price = Math.round((product.basePriceUsd - discount) * 100) / 100;
    promo.usedCount++;
    return { price, discount };
  }

  private isPromoValid(promo: PromoCode): boolean {
    return promo.usedCount < promo.maxUses && promo.expiresAt > new Date();
  }
}
