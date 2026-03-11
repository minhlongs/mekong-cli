export interface Service {
  id: string
  title: string
  description: string
  credits: number
  priceUsd: number
  durationMin: number
  category: 'business' | 'tech' | 'marketing'
}

export const SERVICES: Service[] = [
  {
    id: 'business-plan',
    title: 'Business Plan',
    description: 'Market analysis, revenue model, 12-month roadmap — investor-ready output.',
    credits: 5,
    priceUsd: 25,
    durationMin: 15,
    category: 'business',
  },
  {
    id: 'landing-page',
    title: 'Landing Page',
    description: 'Design + code a responsive landing page, deployed to Cloudflare Pages in 10 minutes.',
    credits: 3,
    priceUsd: 15,
    durationMin: 10,
    category: 'tech',
  },
  {
    id: 'seo-audit',
    title: 'SEO Audit',
    description: 'Comprehensive on-page, off-page, and Core Web Vitals audit — prioritized action list.',
    credits: 3,
    priceUsd: 15,
    durationMin: 10,
    category: 'marketing',
  },
  {
    id: 'competitor-analysis',
    title: 'Competitor Analysis',
    description: 'Research strategy, pricing, strengths and weaknesses of your top 5 competitors.',
    credits: 5,
    priceUsd: 25,
    durationMin: 20,
    category: 'business',
  },
  {
    id: 'build-feature',
    title: 'Build Feature',
    description: 'End-to-end feature development: design, code, test, deploy to production.',
    credits: 5,
    priceUsd: 25,
    durationMin: 30,
    category: 'tech',
  },
  {
    id: 'content-marketing',
    title: 'Content Marketing',
    description: '5 SEO blog posts, 10 social media posts, 1 email newsletter — publishing calendar included.',
    credits: 3,
    priceUsd: 15,
    durationMin: 10,
    category: 'marketing',
  },
]
