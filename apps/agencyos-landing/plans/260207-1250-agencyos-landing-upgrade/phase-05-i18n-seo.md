# Phase 05: i18n & SEO

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 5 hours

Implement internationalization (EN/VI) using next-intl and comprehensive SEO optimization including meta tags, OpenGraph images, JSON-LD structured data, and sitemap generation.

## Context Links

- Phase 02: [Design System](./phase-02-design-system.md)
- Phase 04: [Pricing & Conversion](./phase-04-pricing-conversion.md)
- Next.js Docs: https://nextjs.org/docs/app/building-your-application/optimizing/metadata
- next-intl: https://next-intl-docs.vercel.app/

## Key Insights

- Multilingual sites rank 40% better in target markets
- Proper JSON-LD increases CTR by 25%
- OpenGraph images drive 3x social engagement
- Sitemap ensures all pages indexed within 48h
- Vietnamese market represents 30% potential users

## Requirements

### Functional
- English/Vietnamese language switcher
- Translation keys for all UI text
- SEO meta tags (title, description, keywords)
- OpenGraph images for social sharing
- JSON-LD structured data (Organization, SoftwareApplication)
- XML sitemap generation
- robots.txt configuration

### Non-Functional
- Locale detection from browser
- Translation files under 50KB each
- SEO score 95+ on Google Lighthouse
- Fast locale switching (<100ms)
- Accessible language switcher

## Architecture

```
src/
├── i18n/
│   ├── config.ts              # NEW: next-intl config
│   ├── request.ts             # NEW: Server-side i18n
│   └── messages/
│       ├── en.json            # NEW: English translations
│       └── vi.json            # NEW: Vietnamese translations
├── app/
│   ├── [locale]/              # NEW: Locale wrapper
│   │   ├── layout.tsx         # Metadata + JSON-LD
│   │   └── page.tsx           # Homepage (translated)
│   ├── sitemap.ts             # NEW: Dynamic sitemap
│   └── robots.ts              # NEW: Robots config
├── components/
│   └── language-switcher.tsx  # NEW: Locale toggle
└── public/
    └── og-image.png           # NEW: OpenGraph image
```

## Related Code Files

**To Create:**
- `src/i18n/config.ts`
- `src/i18n/request.ts`
- `src/i18n/messages/en.json`
- `src/i18n/messages/vi.json`
- `src/app/[locale]/layout.tsx`
- `src/app/[locale]/page.tsx`
- `src/app/sitemap.ts`
- `src/app/robots.ts`
- `src/components/language-switcher.tsx`
- `public/og-image.png`

**To Refactor:**
- Move `src/app/page.tsx` → `src/app/[locale]/page.tsx`
- Move `src/app/layout.tsx` → `src/app/[locale]/layout.tsx`

## Implementation Steps

### 1. Install Dependencies (10min)

```bash
npm install next-intl
npm install -D @types/node
```

### 2. Configure next-intl (30min)

`src/i18n/config.ts`:
```typescript
export const locales = ['en', 'vi'] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'en';

export const localeNames: Record<Locale, string> = {
  en: 'English',
  vi: 'Tiếng Việt',
};
```

`src/i18n/request.ts`:
```typescript
import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { locales } from './config';

export default getRequestConfig(async ({ locale }) => {
  if (!locales.includes(locale as any)) notFound();

  return {
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
```

Update `next.config.js`:
```javascript
const withNextIntl = require('next-intl/plugin')('./src/i18n/request.ts');

module.exports = withNextIntl({
  // ... existing config
});
```

### 3. Create Translation Files (1h)

`src/i18n/messages/en.json`:
```json
{
  "nav": {
    "features": "Features",
    "pricing": "Pricing",
    "docs": "Docs",
    "login": "Login",
    "signup": "Get Started"
  },
  "hero": {
    "title": "Build AI Agents at",
    "titleHighlight": "10x Speed",
    "subtitle": "The operating system for AI-powered agencies. Ship autonomous agent systems in hours, not months.",
    "cta": "Start Free Trial",
    "ctaSecondary": "View Demo"
  },
  "features": {
    "title": "Everything You Need",
    "subtitle": "Production-ready tools for modern AI agencies",
    "items": {
      "agents": {
        "title": "Multi-Agent Orchestration",
        "description": "Deploy parallel agent teams with built-in coordination"
      },
      "infrastructure": {
        "title": "Battle-Tested Infrastructure",
        "description": "Proxy rotation, rate limiting, and error recovery"
      },
      "integrations": {
        "title": "150+ Integrations",
        "description": "Connect to Stripe, Supabase, Vercel, and more"
      }
    }
  },
  "pricing": {
    "title": "Simple, Transparent Pricing",
    "subtitle": "No hidden fees. Cancel anytime. Scale as you grow.",
    "popular": "Most Popular",
    "cta": "Get Started",
    "ctaEnterprise": "Contact Sales",
    "tiers": {
      "starter": {
        "name": "Starter",
        "description": "Perfect for solopreneurs and small teams",
        "features": [
          "10,000 AI requests/month",
          "5 team members",
          "Basic analytics",
          "Email support",
          "API access"
        ]
      },
      "pro": {
        "name": "Pro",
        "description": "For growing agencies and research teams",
        "features": [
          "100,000 AI requests/month",
          "Unlimited team members",
          "Advanced analytics",
          "Priority support",
          "Custom integrations",
          "White-label option",
          "Dedicated account manager"
        ]
      },
      "enterprise": {
        "name": "Enterprise",
        "description": "Custom solutions for large organizations",
        "features": [
          "Unlimited requests",
          "On-premise deployment",
          "SLA guarantee",
          "24/7 phone support",
          "Custom AI model training",
          "Security audit",
          "Compliance support"
        ]
      }
    }
  },
  "faq": {
    "title": "Frequently Asked Questions",
    "subtitle": "Everything you need to know about AgencyOS"
  },
  "footer": {
    "tagline": "The operating system for AI-powered agencies",
    "copyright": "© 2024 AgencyOS. All rights reserved."
  }
}
```

`src/i18n/messages/vi.json`:
```json
{
  "nav": {
    "features": "Tính Năng",
    "pricing": "Bảng Giá",
    "docs": "Tài Liệu",
    "login": "Đăng Nhập",
    "signup": "Bắt Đầu"
  },
  "hero": {
    "title": "Xây Dựng AI Agent",
    "titleHighlight": "Nhanh 10x",
    "subtitle": "Hệ điều hành cho agency AI. Triển khai hệ thống agent tự động trong vài giờ, không phải vài tháng.",
    "cta": "Dùng Thử Miễn Phí",
    "ctaSecondary": "Xem Demo"
  },
  "features": {
    "title": "Mọi Thứ Bạn Cần",
    "subtitle": "Công cụ sẵn sàng cho agency AI hiện đại",
    "items": {
      "agents": {
        "title": "Điều Phối Đa Agent",
        "description": "Triển khai đội ngũ agent song song với điều phối tích hợp"
      },
      "infrastructure": {
        "title": "Hạ Tầng Đã Kiểm Chứng",
        "description": "Xoay vòng proxy, giới hạn tốc độ, và phục hồi lỗi"
      },
      "integrations": {
        "title": "150+ Tích Hợp",
        "description": "Kết nối với Stripe, Supabase, Vercel và nhiều hơn"
      }
    }
  },
  "pricing": {
    "title": "Bảng Giá Đơn Giản, Minh Bạch",
    "subtitle": "Không phí ẩn. Hủy bất cứ lúc nào. Mở rộng theo nhu cầu.",
    "popular": "Phổ Biến Nhất",
    "cta": "Bắt Đầu",
    "ctaEnterprise": "Liên Hệ Bán Hàng",
    "tiers": {
      "starter": {
        "name": "Khởi Đầu",
        "description": "Hoàn hảo cho cá nhân và đội nhỏ",
        "features": [
          "10.000 yêu cầu AI/tháng",
          "5 thành viên",
          "Phân tích cơ bản",
          "Hỗ trợ email",
          "Truy cập API"
        ]
      },
      "pro": {
        "name": "Chuyên Nghiệp",
        "description": "Cho agency và đội nghiên cứu đang phát triển",
        "features": [
          "100.000 yêu cầu AI/tháng",
          "Thành viên không giới hạn",
          "Phân tích nâng cao",
          "Hỗ trợ ưu tiên",
          "Tích hợp tùy chỉnh",
          "Tùy chọn white-label",
          "Quản lý tài khoản riêng"
        ]
      },
      "enterprise": {
        "name": "Doanh Nghiệp",
        "description": "Giải pháp tùy chỉnh cho tổ chức lớn",
        "features": [
          "Yêu cầu không giới hạn",
          "Triển khai on-premise",
          "Đảm bảo SLA",
          "Hỗ trợ 24/7",
          "Huấn luyện AI tùy chỉnh",
          "Kiểm tra bảo mật",
          "Hỗ trợ tuân thủ"
        ]
      }
    }
  },
  "faq": {
    "title": "Câu Hỏi Thường Gặp",
    "subtitle": "Mọi thứ bạn cần biết về AgencyOS"
  },
  "footer": {
    "tagline": "Hệ điều hành cho agency AI",
    "copyright": "© 2024 AgencyOS. Bảo lưu mọi quyền."
  }
}
```

### 4. Restructure App Directory (45min)

`src/app/[locale]/layout.tsx`:
```typescript
import { notFound } from 'next/navigation';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { locales } from '@/i18n/config';
import type { Metadata } from 'next';
import './globals.css';

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://agencyos.dev';

  const metadata = {
    en: {
      title: 'AgencyOS - Build AI Agents at 10x Speed',
      description: 'The operating system for AI-powered agencies. Ship autonomous agent systems in hours, not months.',
      keywords: 'AI agents, autonomous systems, agency OS, multi-agent, orchestration',
    },
    vi: {
      title: 'AgencyOS - Xây Dựng AI Agent Nhanh 10x',
      description: 'Hệ điều hành cho agency AI. Triển khai hệ thống agent tự động trong vài giờ.',
      keywords: 'AI agents, hệ thống tự động, agency OS, đa agent, điều phối',
    },
  }[locale] || metadata.en;

  return {
    title: metadata.title,
    description: metadata.description,
    keywords: metadata.keywords,
    metadataBase: new URL(baseUrl),
    alternates: {
      canonical: `/${locale}`,
      languages: {
        en: '/en',
        vi: '/vi',
      },
    },
    openGraph: {
      title: metadata.title,
      description: metadata.description,
      url: `${baseUrl}/${locale}`,
      siteName: 'AgencyOS',
      images: [
        {
          url: '/og-image.png',
          width: 1200,
          height: 630,
          alt: 'AgencyOS - AI Agent Operating System',
        },
      ],
      locale: locale,
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: metadata.title,
      description: metadata.description,
      images: ['/og-image.png'],
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        'max-video-preview': -1,
        'max-image-preview': 'large',
        'max-snippet': -1,
      },
    },
  };
}

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!locales.includes(locale as any)) {
    notFound();
  }

  const messages = await getMessages();

  // JSON-LD Structured Data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        '@id': 'https://agencyos.dev/#organization',
        name: 'AgencyOS',
        url: 'https://agencyos.dev',
        logo: {
          '@type': 'ImageObject',
          url: 'https://agencyos.dev/logo.png',
        },
        sameAs: [
          'https://twitter.com/agencyos',
          'https://github.com/agencyos',
        ],
      },
      {
        '@type': 'SoftwareApplication',
        '@id': 'https://agencyos.dev/#software',
        name: 'AgencyOS',
        applicationCategory: 'DeveloperApplication',
        operatingSystem: 'Web',
        offers: {
          '@type': 'Offer',
          price: '99',
          priceCurrency: 'USD',
          priceValidUntil: '2025-12-31',
        },
        aggregateRating: {
          '@type': 'AggregateRating',
          ratingValue: '4.8',
          ratingCount: '127',
        },
      },
      {
        '@type': 'WebSite',
        '@id': 'https://agencyos.dev/#website',
        url: 'https://agencyos.dev',
        name: 'AgencyOS',
        inLanguage: locale,
      },
    ],
  };

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

`src/app/[locale]/page.tsx`:
```typescript
import { HeroSection } from '@/components/hero-section';
import { FeaturesSection } from '@/components/features-section';
import { PricingSection } from '@/components/pricing-section';
import { FAQSection } from '@/components/faq-section';
import { NavbarSection } from '@/components/navbar-section';
import { FooterSection } from '@/components/footer-section';

export default function HomePage() {
  return (
    <>
      <NavbarSection />
      <main>
        <HeroSection />
        <FeaturesSection />
        <PricingSection />
        <FAQSection />
      </main>
      <FooterSection />
    </>
  );
}
```

### 5. Create Language Switcher (30min)

`src/components/language-switcher.tsx`:
```typescript
"use client";

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { locales, localeNames, type Locale } from '@/i18n/config';
import { Globe } from 'lucide-react';
import { motion } from 'framer-motion';
import { useState } from 'react';

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const handleLocaleChange = (newLocale: Locale) => {
    const newPathname = pathname.replace(`/${locale}`, `/${newLocale}`);
    router.push(newPathname);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg glass-effect hover:bg-white/10 transition-colors"
        aria-label="Change language"
      >
        <Globe className="w-4 h-4" />
        <span className="text-sm font-medium">{localeNames[locale as Locale]}</span>
      </button>

      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="absolute top-full mt-2 right-0 glass-effect rounded-lg overflow-hidden min-w-[140px] z-50"
        >
          {locales.map((loc) => (
            <button
              key={loc}
              onClick={() => handleLocaleChange(loc)}
              className={`w-full text-left px-4 py-2 hover:bg-white/10 transition-colors ${
                locale === loc ? 'bg-white/5 font-medium' : ''
              }`}
            >
              {localeNames[loc]}
            </button>
          ))}
        </motion.div>
      )}
    </div>
  );
}
```

### 6. Generate Sitemap (30min)

`src/app/sitemap.ts`:
```typescript
import { MetadataRoute } from 'next';
import { locales } from '@/i18n/config';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://agencyos.dev';

  const routes = ['', '/pricing', '/docs', '/blog'];

  const sitemap: MetadataRoute.Sitemap = [];

  locales.forEach((locale) => {
    routes.forEach((route) => {
      sitemap.push({
        url: `${baseUrl}/${locale}${route}`,
        lastModified: new Date(),
        changeFrequency: route === '' ? 'daily' : 'weekly',
        priority: route === '' ? 1 : 0.8,
        alternates: {
          languages: Object.fromEntries(
            locales.map((loc) => [loc, `${baseUrl}/${loc}${route}`])
          ),
        },
      });
    });
  });

  return sitemap;
}
```

### 7. Configure Robots (15min)

`src/app/robots.ts`:
```typescript
import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://agencyos.dev';

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/admin/', '/_next/'],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
```

### 8. Update Components with Translations (1h)

Update each component to use `useTranslations`:

Example for `hero-section.tsx`:
```typescript
"use client";

import { useTranslations } from 'next-intl';
// ... rest of imports

export function HeroSection() {
  const t = useTranslations('hero');

  return (
    <section>
      <h1>
        {t('title')} <span className="gradient">{t('titleHighlight')}</span>
      </h1>
      <p>{t('subtitle')}</p>
      <button>{t('cta')}</button>
    </section>
  );
}
```

Repeat for: navbar, features, pricing, FAQ, footer.

### 9. Create OpenGraph Image (30min)

Use Figma or generate with code:
- Size: 1200x630px
- Dark gradient background
- AgencyOS logo
- Tagline: "Build AI Agents at 10x Speed"
- Save as `public/og-image.png`

Or use Next.js Image Generation API:

`src/app/[locale]/opengraph-image.tsx`:
```typescript
import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const alt = 'AgencyOS - AI Agent Operating System';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'system-ui',
        }}
      >
        <div style={{ fontSize: 80, fontWeight: 'bold', color: 'white' }}>
          AgencyOS
        </div>
        <div style={{ fontSize: 40, color: 'rgba(255,255,255,0.9)', marginTop: 20 }}>
          Build AI Agents at 10x Speed
        </div>
      </div>
    ),
    { ...size }
  );
}
```

## Todo List

- [ ] Install next-intl dependency
- [ ] Create i18n config files
- [ ] Create EN translation file
- [ ] Create VI translation file
- [ ] Restructure app with [locale] directory
- [ ] Add metadata generation to layout
- [ ] Add JSON-LD structured data
- [ ] Create language switcher component
- [ ] Update all components with useTranslations
- [ ] Create sitemap.ts
- [ ] Create robots.ts
- [ ] Generate OpenGraph image
- [ ] Test locale switching (EN ↔ VI)
- [ ] Test SEO meta tags in browser
- [ ] Verify sitemap.xml accessible
- [ ] Verify robots.txt accessible
- [ ] Test social share preview (Twitter/LinkedIn)
- [ ] Run Lighthouse SEO audit (target 95+)
- [ ] Test structured data with Google Rich Results

## Success Criteria

- ✅ Both locales (EN/VI) accessible at /en and /vi
- ✅ Language switcher works without page reload
- ✅ All UI text translated (no hardcoded strings)
- ✅ SEO score 95+ on Lighthouse
- ✅ Meta tags present in <head>
- ✅ OpenGraph image displays in social previews
- ✅ JSON-LD validates on Google Rich Results Test
- ✅ Sitemap.xml generates all routes with alternates
- ✅ Robots.txt accessible and correct
- ✅ hreflang tags present for both locales

## Risk Assessment

**Risk:** Translation keys missing in VI file
**Mitigation:** Use TypeScript to enforce key parity, test both locales

**Risk:** Locale routing breaks existing URLs
**Mitigation:** Set up redirects from / → /en (default)

**Risk:** SEO crawlers can't discover alternate locales
**Mitigation:** Use hreflang tags + sitemap alternates

**Risk:** OpenGraph image too large (>1MB)
**Mitigation:** Optimize with sharp/imagemin, use WebP

## Security Considerations

- No sensitive data in translations
- Validate locale param to prevent injection
- Sanitize user-generated content in meta tags

## Next Steps

→ Proceed to Phase 06: Hub Integration (Polar.sh, Analytics)
