import { describe, expect, it } from 'vitest'
import type { D1Database } from '@cloudflare/workers-types'
import server from '../src/index'

const db = {} as D1Database
const facebookSecret = 'local-test-facebook-app-secret'

async function signFacebookBody(body: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const signature = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(body))
  const hex = Array.from(new Uint8Array(signature))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
  return `sha256=${hex}`
}

describe('chat webhook authentication', () => {
  it('does not accept the former public Facebook verification token', async () => {
    const url = new URL('http://localhost/v1/chat/webhook/facebook')
    url.searchParams.set('hub.mode', 'subscribe')
    url.searchParams.set('hub.verify_token', 'mekong_verify')
    url.searchParams.set('hub.challenge', 'challenge')

    const response = await server.fetch(new Request(url), {})
    expect(response.status).toBe(403)
  })

  it('accepts Facebook subscription verification only with the configured secret', async () => {
    const url = new URL('http://localhost/v1/chat/webhook/facebook')
    url.searchParams.set('hub.mode', 'subscribe')
    url.searchParams.set('hub.verify_token', 'facebook-verify-secret')
    url.searchParams.set('hub.challenge', 'challenge')

    const response = await server.fetch(new Request(url), { FB_VERIFY_TOKEN: 'facebook-verify-secret' })
    expect(response.status).toBe(200)
    expect(await response.text()).toBe('challenge')
  })

  it('fails closed when Facebook webhook signing is not configured', async () => {
    const body = JSON.stringify({ object: 'page', entry: [] })
    const response = await server.fetch(new Request('http://localhost/v1/chat/webhook/facebook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    }), { DB: db })

    expect(response.status).toBe(503)
  })

  it('rejects Facebook callbacks without a signature', async () => {
    const body = JSON.stringify({ object: 'page', entry: [] })
    const response = await server.fetch(new Request('http://localhost/v1/chat/webhook/facebook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    }), { DB: db, FB_APP_SECRET: facebookSecret })

    expect(response.status).toBe(401)
  })

  it('rejects Facebook callbacks with an invalid signature', async () => {
    const body = JSON.stringify({ object: 'page', entry: [] })
    const response = await server.fetch(new Request('http://localhost/v1/chat/webhook/facebook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Hub-Signature-256': 'sha256=00' },
      body,
    }), { DB: db, FB_APP_SECRET: facebookSecret })

    expect(response.status).toBe(401)
  })

  it('accepts validly signed Facebook callbacks', async () => {
    const body = JSON.stringify({ object: 'page', entry: [] })
    const signature = await signFacebookBody(body, facebookSecret)
    const response = await server.fetch(new Request('http://localhost/v1/chat/webhook/facebook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Hub-Signature-256': signature },
      body,
    }), { DB: db, FB_APP_SECRET: facebookSecret })

    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ received: true })
  })

  it('fails closed for Zalo callbacks without a signing secret or signature', async () => {
    const body = JSON.stringify({
      event_name: 'user_send_text', app_id: 'app',
      sender: { id: 'sender' }, recipient: { id: 'recipient' },
      message: { text: 'hello', msg_id: 'message-1' }, timestamp: '1',
    })
    const noSecret = await server.fetch(new Request('http://localhost/v1/chat/webhook/zalo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body,
    }), { DB: db })
    const noSignature = await server.fetch(new Request('http://localhost/v1/chat/webhook/zalo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body,
    }), { DB: db, ZALO_APP_SECRET: 'local-test-zalo-secret' })

    expect(noSecret.status).toBe(503)
    expect(noSignature.status).toBe(401)
  })
})
