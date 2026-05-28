import { describe, it, expect, vi, beforeEach } from 'vitest';
import { safeCompare, verifySignature } from '../src/crypto';
import { regexFallbackParser } from '../src/parser';
import app from '../src/index';

// Helper to compute HMAC SHA-256 using Node's crypto for test validation
import crypto from 'crypto';
function computeHmacSignature(appId: string, rawBody: string, timestamp: string, secretKey: string): string {
  const data = `${appId}${rawBody}${timestamp}${secretKey}`;
  return crypto.createHmac('sha256', secretKey).update(data).digest('hex');
}

describe('Zalo Lead Parser Test Suite', () => {
  const secretKey = 'test_secret_key';
  const appId = '123456789';
  const timestamp = '1716301234';

  describe('Cryptographic Signature Verification', () => {
    it('should compare strings in constant-time safely', () => {
      expect(safeCompare('abc', 'abc')).toBe(true);
      expect(safeCompare('abc', 'def')).toBe(false);
      expect(safeCompare('abc', 'abcd')).toBe(false);
    });

    it('should verify correct signature successfully', async () => {
      const payload = {
        app_id: appId,
        timestamp: timestamp,
        sender: { id: 'user_1' },
        recipient: { id: 'oa_1' },
        event_name: 'user_send_text',
        message: { text: 'hello', msg_id: 'msg_1' }
      };
      const rawBody = JSON.stringify(payload);
      const signature = computeHmacSignature(appId, rawBody, timestamp, secretKey);

      const isValid = await verifySignature(signature, rawBody, secretKey);
      expect(isValid).toBe(true);
    });

    it('should reject incorrect signatures', async () => {
      const payload = { app_id: appId, timestamp: timestamp };
      const rawBody = JSON.stringify(payload);
      const isValid = await verifySignature('wrong_signature', rawBody, secretKey);
      expect(isValid).toBe(false);
    });
  });

  describe('Fallback Text Parser', () => {
    it('should extract Vietnamese phone numbers successfully', () => {
      const text = 'Tôi muốn tìm mua căn hộ. Liên hệ 0908765432';
      const parsed = regexFallbackParser(text);
      expect(parsed.phone).toBe('0908765432');
      expect(parsed.intent).toBe('warm');
    });

    it('should classify greetings as cold intent', () => {
      const text = 'hello';
      const parsed = regexFallbackParser(text);
      expect(parsed.phone).toBeNull();
      expect(parsed.intent).toBe('cold');
    });

    it('should classify ads as junk intent', () => {
      const text = 'Hãy xem quảng cáo này';
      const parsed = regexFallbackParser(text);
      expect(parsed.intent).toBe('junk');
    });
  });

  describe('Hono Route Handler Endpoints', () => {
    let mockDB: any;
    let mockAI: any;
    let mockEnv: any;

    beforeEach(() => {
      mockDB = {
        prepare: vi.fn().mockReturnValue({
          bind: vi.fn().mockReturnValue({
            run: vi.fn().mockResolvedValue({ success: true })
          })
        })
      };

      mockAI = {
        run: vi.fn().mockResolvedValue({
          response: JSON.stringify({
            name: 'Nam',
            phone: '0901234567',
            area: 'Quận 2',
            price: '5 tỷ',
            intent: 'warm'
          })
        })
      };

      mockEnv = {
        DB: mockDB,
        AI: mockAI,
        ZALO_OA_SECRET_KEY: secretKey
      };
    });

    it('should return health status for GET /', async () => {
      const res = await app.request('/');
      expect(res.status).toBe(200);
      const json = await res.json() as any;
      expect(json.status).toBe('healthy');
    });

    it('should return 401 for post without signature or invalid signature', async () => {
      const res = await app.request('/webhook', {
        method: 'POST',
        body: JSON.stringify({ event_name: 'test' }),
        headers: { 'X-ZEvent-Signature': 'invalid' }
      }, mockEnv);

      expect(res.status).toBe(401);
    });

    it('should process webhook event successfully with valid signature', async () => {
      const payload = {
        app_id: appId,
        timestamp: timestamp,
        sender: { id: 'user_1' },
        recipient: { id: 'oa_1' },
        event_name: 'user_send_text',
        message: { text: 'Tôi muốn mua nhà ở Quận 2. Sđt: 0901234567. Tên là Nam.', msg_id: 'msg_1' }
      };

      const rawBody = JSON.stringify(payload);
      const signature = computeHmacSignature(appId, rawBody, timestamp, secretKey);

      const res = await app.request('/webhook', {
        method: 'POST',
        body: rawBody,
        headers: {
          'Content-Type': 'application/json',
          'X-ZEvent-Signature': signature
        }
      }, mockEnv);

      expect(res.status).toBe(200);
      const json = await res.json() as any;
      expect(json.status).toBe('success');
      expect(json.processed).toBe(true);
      expect(json.parsedLead.name).toBe('Nam');
      expect(json.parsedLead.phone).toBe('0901234567');
      expect(json.parsedLead.area).toBe('Quận 2');
      expect(json.parsedLead.price).toBe('5 tỷ');
      expect(json.parsedLead.intent).toBe('warm');

      expect(mockDB.prepare).toHaveBeenCalled();
    });
  });
});
