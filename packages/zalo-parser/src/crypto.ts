import { ZaloWebhookPayload } from './types';

/**
 * Constant-time string comparison to prevent timing attacks.
 */
export function safeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

/**
 * Verifies Zalo OA Webhook X-ZEvent-Signature.
 * Zalo signature algorithm: HMAC-SHA256 of (appId + rawBody + timestamp + secretKey) signed with secretKey.
 */
export async function verifySignature(
  signature: string,
  rawBody: string,
  secretKey: string
): Promise<boolean> {
  if (!signature || !rawBody || !secretKey) {
    return false;
  }

  let payload: ZaloWebhookPayload;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return false;
  }

  const appId = payload.app_id || '';
  const timestamp = payload.timestamp || '';
  
  if (!appId || !timestamp) {
    return false;
  }

  const dataToSign = `${appId}${rawBody}${timestamp}${secretKey}`;
  const encoder = new TextEncoder();
  
  try {
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secretKey),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    
    const signatureBuffer = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(dataToSign)
    );
    
    const calculatedSignature = Array.from(new Uint8Array(signatureBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
      
    return safeCompare(signature, calculatedSignature);
  } catch (error) {
    console.error('Signature verification error:', error);
    return false;
  }
}
