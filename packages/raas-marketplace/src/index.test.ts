import { describe, it, expect } from 'vitest'
import { ProductCatalog } from './catalog.js'
import { generateStorefrontHTML, generateStorefrontJSON, generateEmbedWidget, handleStorefrontRequest } from './storefront.js'

describe('ProductCatalog', () => {
  it('should have 3 default products', () => {
    const catalog = new ProductCatalog()
    const products = catalog.listProducts()
    expect(products).toHaveLength(3)
  })

  it('should filter by tier', () => {
    const catalog = new ProductCatalog()
    const pro = catalog.listProducts({ tier: 'pro' })
    expect(pro).toHaveLength(1)
    expect(pro[0].id).toBe('openclaw-pro')
  })

  it('should filter active products', () => {
    const catalog = new ProductCatalog()
    const active = catalog.listProducts({ active: true })
    expect(active).toHaveLength(3)
  })

  it('should get product by id', () => {
    const catalog = new ProductCatalog()
    const p = catalog.getProduct('openclaw-starter')
    expect(p).toBeDefined()
    expect(p!.basePriceUsd).toBe(49)
  })

  it('should return undefined for unknown product', () => {
    const catalog = new ProductCatalog()
    expect(catalog.getProduct('nonexistent')).toBeUndefined()
  })

  it('should calculate base price', () => {
    const catalog = new ProductCatalog()
    expect(catalog.calculatePrice('openclaw-starter')).toBe(49)
  })

  it('should apply quantity discount', () => {
    const catalog = new ProductCatalog()
    // 2 units = 5% discount: 49 * 2 * 0.95 = 93.1
    const price = catalog.calculatePrice('openclaw-starter', { quantity: 2 })
    expect(price).toBe(93.1)
  })

  it('should cap quantity discount at 30%', () => {
    const catalog = new ProductCatalog()
    // 10 units = 45% would be > 30%, so cap at 30%: 49 * 10 * 0.7 = 343
    const price = catalog.calculatePrice('openclaw-starter', { quantity: 10 })
    expect(price).toBe(343)
  })

  it('should apply promo code', () => {
    const catalog = new ProductCatalog()
    catalog.addPromo({
      code: 'LAUNCH20',
      discountPercent: 20,
      expiresAt: new Date(Date.now() + 86400000),
      maxUses: 100,
      usedCount: 0,
    })
    const price = catalog.calculatePrice('openclaw-starter', { promoCode: 'LAUNCH20' })
    expect(price).toBe(39.2) // 49 * 0.8
  })

  it('should reject expired promo', () => {
    const catalog = new ProductCatalog()
    catalog.addPromo({
      code: 'EXPIRED',
      discountPercent: 50,
      expiresAt: new Date(Date.now() - 86400000),
      maxUses: 100,
      usedCount: 0,
    })
    const price = catalog.calculatePrice('openclaw-starter', { promoCode: 'EXPIRED' })
    expect(price).toBe(49) // no discount
  })

  it('should throw for unknown product price', () => {
    const catalog = new ProductCatalog()
    expect(() => catalog.calculatePrice('nope')).toThrow('Product not found')
  })
})

describe('Storefront', () => {
  it('should generate HTML with product cards', () => {
    const catalog = new ProductCatalog()
    const html = generateStorefrontHTML(catalog.listProducts({ active: true }))
    expect(html).toContain('OpenClaw Starter')
    expect(html).toContain('OpenClaw Pro')
    expect(html).toContain('$49')
    expect(html).toContain('/checkout?product=openclaw-starter')
  })

  it('should generate JSON response', () => {
    const catalog = new ProductCatalog()
    const json = generateStorefrontJSON(catalog.listProducts({ active: true })) as any
    expect(json.success).toBe(true)
    expect(json.data).toHaveLength(3)
    expect(json.count).toBe(3)
    expect(json.data[0].checkoutUrl).toContain('/checkout')
  })

  it('should generate embed widget', () => {
    const catalog = new ProductCatalog()
    const widget = generateEmbedWidget(catalog.listProducts({ active: true }))
    expect(widget).toContain('openclaw-widget')
    expect(widget).toContain('$49/mo')
  })

  it('should handle /products request', () => {
    const catalog = new ProductCatalog()
    const res = handleStorefrontRequest('/products', catalog)
    expect(res.status).toBe(200)
    expect(res.contentType).toBe('application/json')
    const body = JSON.parse(res.body)
    expect(body.success).toBe(true)
  })

  it('should handle /products/:id request', () => {
    const catalog = new ProductCatalog()
    const res = handleStorefrontRequest('/products/openclaw-pro', catalog)
    expect(res.status).toBe(200)
    const body = JSON.parse(res.body)
    expect(body.data.id).toBe('openclaw-pro')
  })

  it('should return 404 for unknown product', () => {
    const catalog = new ProductCatalog()
    const res = handleStorefrontRequest('/products/nonexistent', catalog)
    expect(res.status).toBe(404)
  })

  it('should return 404 for unknown path', () => {
    const catalog = new ProductCatalog()
    const res = handleStorefrontRequest('/unknown', catalog)
    expect(res.status).toBe(404)
  })
})
