import { describe, expect, it } from 'vitest'
import server from '../src/index'

describe('Vietnamese payment endpoints remain sandbox-only', () => {
  it('does not issue mock URLs on production provider hosts', async () => {
    const response = await server.fetch(new Request('http://localhost/payment/create', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        method: 'momo',
        tenant_id: 'demo-tenant',
        amount: 1000,
        credits: 1,
      }),
    }), {})

    expect(response.status).toBe(503)
    const body = await response.json() as { error: { code: string; message: string } }
    expect(body.error.code).toBe('PAYMENT_SANDBOX_ONLY')
    expect(body.error.message).toContain('verified sandbox integration')
    expect(body).not.toHaveProperty('payment_url')
  })

  it('does not accept unsigned provider callbacks or credit accounts', async () => {
    const momoResponse = await server.fetch(new Request('http://localhost/payment/momo/ipn', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ resultCode: 0, extraData: 'forged', amount: 1 }),
    }), {})
    const vnpayResponse = await server.fetch(new Request('http://localhost/payment/vnpay/ipn?vnp_ResponseCode=00&vnp_OrderInfo=forged&vnp_Amount=100000'), {})

    expect(momoResponse.status).toBe(503)
    expect(vnpayResponse.status).toBe(503)
    expect((await momoResponse.json()).error.code).toBe('PAYMENT_SANDBOX_ONLY')
    expect((await vnpayResponse.json()).error.code).toBe('PAYMENT_SANDBOX_ONLY')
  })
})
