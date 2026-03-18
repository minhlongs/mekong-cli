import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  site: 'https://dashboard.agencyos.network',
  i18n: {
    defaultLocale: 'vi',
    locales: ['vi', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
