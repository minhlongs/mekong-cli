import axios from 'axios'
import type {
  MarketplacePlugin,
  Category,
  PluginDetail,
  SearchPluginsParams,
  CheckoutSession,
  License,
} from '../types/marketplace'

export type { SearchPluginsParams } from '../types/marketplace'

declare global {
  interface ImportMeta {
    readonly VITE_MARKETPLACE_API_URL?: string
  }
}

const API_BASE_URL = import.meta.env.VITE_MARKETPLACE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface MarketplaceService {
  // Search & Discovery
  searchPlugins(params: SearchPluginsParams): Promise<{
    total: number
    page: number
    page_size: number
    total_pages: number
    plugins: MarketplacePlugin[]
  }>
  getPlugin(name: string): Promise<MarketplacePlugin>
  getPluginDetail(name: string): Promise<PluginDetail>
  getFeatured(limit?: number): Promise<MarketplacePlugin[]>
  getTrending(limit?: number): Promise<MarketplacePlugin[]>
  getCategories(): Promise<Category[]>
  getTags(): Promise<{ tags: Array<{ tag: string; count: number }> }>
  getStats(): Promise<any>

  // Installation
  getInstallInfo(pluginName: string, version?: string): Promise<{
    download_url: string
    checksum: string
    install_command: string
  }>

  // Publishing
  publishPlugin(
    manifestBase64: string,
    metadata: {
      name: string
      version: string
      description: string
      author: string
      category?: string
      tags?: string[]
    }
  ): Promise<{ plugin_id: string; status: string }>

  // Ratings
  ratePlugin(pluginName: string, rating: number, comment?: string): Promise<{ success: boolean }>
  getPluginRatings(pluginName: string, limit?: number): Promise<any>

  // Payments
  createCheckout(
    pluginId: string,
    userId: string,
    userEmail: string,
    tier: string,
    successUrl: string,
    cancelUrl: string
  ): Promise<CheckoutSession>
  completePurchase(
    sessionId: string,
    provider: 'stripe' | 'polar',
    eventData?: any
  ): Promise<{
    payment_id: string
    license_key: string
    plugin_id: string
    tier: string
    user_id: string
    amount: number
    currency: string
    developer_commission: number
  }>

  // Licenses
  listUserLicenses(userId: string): Promise<{ user_id: string; licenses: License[]; count: number }>
  validateLicense(licenseKey: string, pluginId?: string): Promise<{
    valid: boolean
    plugin_id?: string
    tier?: string
    user_id?: string
    issued_at?: string
    expires_at?: string
    error?: string
  }>

  // Developer
  getDeveloperPayoutInfo(developerId: string): Promise<any>
  listMyPlugins(): Promise<MarketplacePlugin[]>
}

export const marketplaceService: MarketplaceService = {
  // Search
  async searchPlugins(params: SearchPluginsParams) {
    const response = await api.get('/marketplace/plugins', { params })
    return response.data
  },

  async getPlugin(name: string) {
    const response = await api.get(`/marketplace/plugins/${encodeURIComponent(name)}`)
    return response.data
  },

  async getPluginDetail(name: string) {
    const response = await api.get(`/marketplace/plugins/${encodeURIComponent(name)}/detail`)
    return response.data
  },

  async getFeatured(limit = 10) {
    const response = await api.get(`/marketplace/plugins/featured?limit=${limit}`)
    return response.data
  },

  async getTrending(limit = 10) {
    const response = await api.get(`/marketplace/plugins/trending?limit=${limit}`)
    return response.data
  },

  async getCategories() {
    const response = await api.get('/marketplace/categories')
    return response.data.categories
  },

  async getTags() {
    const response = await api.get('/marketplace/tags')
    return response.data
  },

  async getStats() {
    const response = await api.get('/marketplace/stats')
    return response.data
  },

  // Installation
  async getInstallInfo(pluginName: string, version?: string) {
    const url = `/marketplace/plugins/${encodeURIComponent(pluginName)}/install${version ? `?version=${version}` : ''}`
    const response = await api.get(url)
    return response.data
  },

  // Publishing
  async publishPlugin(manifestBase64: string, metadata: any) {
    const response = await api.post('/marketplace/plugins', {
      manifest_base64: manifestBase64,
      ...metadata,
    })
    return response.data
  },

  // Ratings
  async ratePlugin(pluginName: string, rating: number, comment?: string) {
    const response = await api.post(`/marketplace/plugins/${encodeURIComponent(pluginName)}/rate`, {
      rating,
      comment,
    })
    return response.data
  },

  async getPluginRatings(pluginName: string, limit = 20) {
    const response = await api.get(`/marketplace/plugins/${encodeURIComponent(pluginName)}/ratings?limit=${limit}`)
    return response.data
  },

  // Payments
  async createCheckout(
    pluginId: string,
    userId: string,
    userEmail: string,
    tier: string,
    successUrl: string,
    cancelUrl: string
  ) {
    const response = await api.post(`/marketplace/plugins/${encodeURIComponent(pluginId)}/checkout`, {
      user_id: userId,
      user_email: userEmail,
      tier,
      success_url: successUrl,
      cancel_url: cancelUrl,
    })
    return response.data
  },

  async completePurchase(sessionId: string, provider: 'stripe' | 'polar', eventData?: any) {
    const response = await api.post(`/marketplace/plugins/purchase/complete`, {
      session_id: sessionId,
      provider,
      event_data: eventData,
    })
    return response.data
  },

  // Licenses
  async listUserLicenses(userId: string) {
    const response = await api.get(`/marketplace/purchases/${userId}/licenses`)
    return response.data
  },

  async validateLicense(licenseKey: string, pluginId?: string) {
    const response = await api.post(`/marketplace/licenses/${encodeURIComponent(licenseKey)}/validate`, {
      plugin_id: pluginId,
    })
    return response.data
  },

  // Developer
  async getDeveloperPayoutInfo(developerId: string) {
    const response = await api.get(`/marketplace/developers/${developerId}/payouts`)
    return response.data
  },

  async listMyPlugins() {
    const response = await api.get('/marketplace/my/plugins')
    return response.data
  },
}

export default api
