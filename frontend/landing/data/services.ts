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
    title: 'Kế hoạch kinh doanh',
    description: 'Phân tích thị trường, mô hình doanh thu, roadmap 12 tháng — sẵn sàng gửi nhà đầu tư.',
    credits: 5,
    priceUsd: 25,
    durationMin: 15,
    category: 'business',
  },
  {
    id: 'landing-page',
    title: 'Landing Page',
    description: 'Thiết kế + code landing page responsive, deploy lên Cloudflare Pages trong 10 phút.',
    credits: 3,
    priceUsd: 15,
    durationMin: 10,
    category: 'tech',
  },
  {
    id: 'seo-audit',
    title: 'SEO Audit',
    description: 'Kiểm tra toàn diện on-page, off-page, Core Web Vitals — danh sách ưu tiên sửa ngay.',
    credits: 3,
    priceUsd: 15,
    durationMin: 10,
    category: 'marketing',
  },
  {
    id: 'competitor-analysis',
    title: 'Phân tích đối thủ',
    description: 'Nghiên cứu chiến lược, định giá, điểm mạnh yếu của top 5 đối thủ cạnh tranh.',
    credits: 5,
    priceUsd: 25,
    durationMin: 20,
    category: 'business',
  },
  {
    id: 'build-feature',
    title: 'Build Feature',
    description: 'Phát triển tính năng mới end-to-end: thiết kế → code → test → deploy production.',
    credits: 5,
    priceUsd: 25,
    durationMin: 30,
    category: 'tech',
  },
  {
    id: 'content-marketing',
    title: 'Content Marketing',
    description: '5 bài blog SEO, 10 posts mạng xã hội, 1 email newsletter — lịch đăng sẵn sàng.',
    credits: 3,
    priceUsd: 15,
    durationMin: 10,
    category: 'marketing',
  },
]
