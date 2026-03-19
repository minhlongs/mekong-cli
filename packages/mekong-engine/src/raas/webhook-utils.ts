/**
 * Verify Polar.sh webhook signature using HMAC-SHA256
 *
 * @param body - Parsed webhook request body
 * @param signature - X-Polar-Signature header value
 * @param secret - POLAR_WEBHOOK_SECRET environment variable
 * @returns true if signature is valid
 */
export async function verifyPolarSignature(
  body: unknown,
  signature: string | undefined,
  secret: string | undefined,
): Promise<boolean> {
  if (!signature || !secret) return false

  // Polar signature format: "v1=<hmac>"
  const parts = signature.split(',')
  const timestampPart = parts.find(p => p.startsWith('t='))
  const signaturePart = parts.find(p => p.startsWith('v1='))

  if (!timestampPart || !signaturePart) return false

  const timestamp = parseInt(timestampPart.slice(2), 10)
  if (isNaN(timestamp)) return false
  const providedSignature = signaturePart.slice(3)

  // Reject if timestamp is older than 5 minutes (replay attack prevention)
  const now = Math.floor(Date.now() / 1000)
  if (now - timestamp > 300) return false

  // Build signed payload (timestamp + body)
  const bodyStr = JSON.stringify(body)
  const signedPayload = `${timestamp}.${bodyStr}`

  // Calculate HMAC-SHA256 using global crypto (Cloudflare Workers compatible)
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )

  const signatureBuffer = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(signedPayload)
  )

  const calculatedSignature = Array.from(new Uint8Array(signatureBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')

  // Constant-time comparison to prevent timing attacks
  return constantTimeCompare(calculatedSignature, providedSignature)
}

/**
 * Constant-time string comparison to prevent timing attacks
 */
function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }
  return result === 0
}
