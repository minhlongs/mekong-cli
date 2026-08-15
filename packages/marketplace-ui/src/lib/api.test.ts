import { describe, it, expect } from 'vitest'
import { marketplaceService } from '../lib/api'
import type { SearchPluginsParams } from '../types/marketplace'

describe('Marketplace API Service', () => {
  it('should have all required methods defined', () => {
    expect(typeof marketplaceService.searchPlugins).toBe('function')
    expect(typeof marketplaceService.getPlugin).toBe('function')
    expect(typeof marketplaceService.getPluginDetail).toBe('function')
    expect(typeof marketplaceService.getFeatured).toBe('function')
    expect(typeof marketplaceService.getTrending).toBe('function')
    expect(typeof marketplaceService.getCategories).toBe('function')
    expect(typeof marketplaceService.getTags).toBe('function')
    expect(typeof marketplaceService.getStats).toBe('function')
    expect(typeof marketplaceService.getInstallInfo).toBe('function')
    expect(typeof marketplaceService.publishPlugin).toBe('function')
    expect(typeof marketplaceService.ratePlugin).toBe('function')
    expect(typeof marketplaceService.getPluginRatings).toBe('function')
    expect(typeof marketplaceService.createCheckout).toBe('function')
    expect(typeof marketplaceService.completePurchase).toBe('function')
    expect(typeof marketplaceService.listUserLicenses).toBe('function')
    expect(typeof marketplaceService.validateLicense).toBe('function')
    expect(typeof marketplaceService.getDeveloperPayoutInfo).toBe('function')
    expect(typeof marketplaceService.listMyPlugins).toBe('function')
  })

  it('should accept valid SearchPluginsParams', async () => {
    const params: SearchPluginsParams = {
      q: 'test',
      page: 1,
      page_size: 20,
      sort_by: 'download_count',
      sort_order: 'desc',
    }
    expect(params.q).toBe('test')
    expect(params.page).toBe(1)
  })
})
