import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  output: 'static',
  site: 'https://agencyos.network',
  i18n: {
    defaultLocale: 'vi',
    locales: ['vi', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [sitemap({ changefreq: 'weekly', priority: 0.7 })],
  trailingSlash: 'never',
});
