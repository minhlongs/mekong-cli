# @openclaw/raas-marketplace

Marketplace SDK for the Mekong RaaS platform. Product catalog, storefront generation, sales bot, analytics, affiliate program, and skill registry.

## Install

```bash
npm install @openclaw/raas-marketplace
```

## Modules

### Product Catalog

```typescript
import { ProductCatalog } from '@openclaw/raas-marketplace';

const catalog = new ProductCatalog();
catalog.addProduct({ id: 'skill-seo', name: 'SEO Agent', price: 29 });
const products = catalog.list({ category: 'marketing' });
```

### Storefront

```typescript
import { generateStorefrontHTML, handleStorefrontRequest } from '@openclaw/raas-marketplace/storefront';

const html = generateStorefrontHTML(catalog.list());
const json = generateStorefrontJSON(catalog.list());
```

### Sales Bot

```typescript
import { SalesBot } from '@openclaw/raas-marketplace/sales-bot';

const bot = new SalesBot();
const score = bot.scoreLead({ email: 'ceo@agency.com', company: 'BigCorp' });
const email = bot.generateFollowUp(score);
```

### Analytics

```typescript
import { SalesAnalytics } from '@openclaw/raas-marketplace/analytics';

const analytics = new SalesAnalytics();
analytics.track({ type: 'purchase', productId: 'skill-seo', amount: 29 });
const funnel = analytics.getFunnel();
```

### Affiliate Program

```typescript
import { AffiliateProgram } from '@openclaw/raas-marketplace/affiliate';

const program = new AffiliateProgram();
const stats = program.getStats('affiliate-123');
const commission = program.calculateCommission('affiliate-123');
```

### Skill Registry

```typescript
import { SkillRegistry } from '@openclaw/raas-marketplace';

const registry = new SkillRegistry();
registry.publish(manifest);
const results = registry.search({ query: 'seo', limit: 10 });
const popular = registry.getPopular(5);
```

## License

MIT
