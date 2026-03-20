/**
 * Cryptographic utilities for secure data handling
 */

/**
 * Constant-time string comparison to prevent timing attacks
 * Compares two hex strings in constant time
 */
export function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }
  return result === 0
}

/**
 * Encrypt payment metadata using AES-GCM
 * @param data - Object to encrypt
 * @param secret - Encryption secret (32 bytes for AES-256-GCM)
 */
export async function encryptPaymentMetadata(
  data: Record<string, unknown>,
  secret: string
): Promise<string> {
  const encoder = new TextEncoder()
  const keyData = encoder.encode(secret)

  // Derive key using HKDF
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    keyData,
    'HKDF',
    false,
    ['deriveKey']
  )

  const key = await crypto.subtle.deriveKey(
    {
      name: 'HKDF',
      hash: 'SHA-256',
      salt: encoder.encode('mekong-payment-salt'),
      info: encoder.encode('payment-metadata-encryption')
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt']
  )

  const iv = crypto.getRandomValues(new Uint8Array(12))
  const encoded = encoder.encode(JSON.stringify(data))

  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoded
  )

  // Combine IV + encrypted data, then base64url encode
  const combined = new Uint8Array(iv.length + encrypted.byteLength)
  combined.set(iv, 0)
  combined.set(new Uint8Array(encrypted), iv.length)

  return btoa(String.fromCharCode(...combined))
}

/**
 * Decrypt payment metadata
 * @param token - Encrypted token
 * @param secret - Decryption secret
 */
export async function decryptPaymentMetadata(
  token: string,
  secret: string
): Promise<Record<string, unknown>> {
  try {
    const combined = Uint8Array.from(atob(token), c => c.charCodeAt(0))
    const iv = combined.slice(0, 12)
    const encrypted = combined.slice(12)

    // Derive key (same as encrypt)
    const encoder = new TextEncoder()
    const keyData = encoder.encode(secret)
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      keyData,
      'HKDF',
      false,
      ['deriveKey']
    )

    const key = await crypto.subtle.deriveKey(
      {
        name: 'HKDF',
        hash: 'SHA-256',
        salt: encoder.encode('mekong-payment-salt'),
        info: encoder.encode('payment-metadata-encryption')
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['decrypt']
    )

    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      encrypted
    )

    return JSON.parse(new TextDecoder().decode(decrypted))
  } catch (error) {
    console.error('Failed to decrypt payment metadata:', error)
    throw new Error('Invalid or tampered payment metadata')
  }
}
