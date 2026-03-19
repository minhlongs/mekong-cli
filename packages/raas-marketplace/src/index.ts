export {
  ProductCatalog,
  type Product,
  type PromoCode,
  type PricingContext,
  type ProductFilter,
} from "./catalog.js";

export {
  generateStorefrontHTML,
  generateStorefrontJSON,
  generateEmbedWidget,
  handleStorefrontRequest,
  type StorefrontResponse,
} from "./storefront.js";

export {
  SalesBot,
  type Lead,
  type LeadScore,
  type FollowUpEmail,
} from "./sales-bot.js";

export {
  SalesAnalytics,
  type SalesEvent,
  type SalesEventType,
  type FunnelStep,
} from "./analytics.js";

export {
  AffiliateProgram,
  type CommissionSummary,
  type AffiliateStats,
} from "./affiliate.js";
