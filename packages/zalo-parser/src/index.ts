import { Hono } from 'hono';
import { Env, ZaloWebhookPayload } from './types';
import { verifySignature } from './crypto';
import { parseLead } from './parser';

const app = new Hono<{ Bindings: Env }>();

// Simple health check route
app.get('/', (c) => {
  return c.json({
    status: 'healthy',
    service: 'zalo-lead-parser-microservice',
    timestamp: new Date().toISOString()
  });
});

// Zalo webhook receiver endpoint
app.post('/webhook', async (c) => {
  const signature = c.req.header('X-ZEvent-Signature') || '';
  
  // Clone raw request body to allow multiple reads (validation and parsing)
  let rawBody: string;
  try {
    rawBody = await c.req.text();
  } catch (error) {
    return c.json({ error: 'Failed to read raw request body' }, 400);
  }

  // Retrieve secret key from environment
  const secretKey = c.env.ZALO_OA_SECRET_KEY || 'mock_secret_for_local_dev';

  // Cryptographic Signature verification
  const isValid = await verifySignature(signature, rawBody, secretKey);
  if (!isValid) {
    return c.json({ error: 'Unauthorized: Invalid signature' }, 401);
  }

  // Parse webhook payload
  let payload: ZaloWebhookPayload;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return c.json({ error: 'Bad Request: Invalid JSON payload' }, 400);
  }

  // Process text messages sent by user to OA
  if (payload.event_name === 'user_send_text' && payload.message) {
    const zaloUserId = payload.sender.id;
    const text = payload.message.text;
    
    // Call Workers AI parsing engine
    const lead = await parseLead(c.env, text);

    // Persist extracted lead fields to Cloudflare D1 SQLite database (UPSERT on conflict)
    const uuid = crypto.randomUUID();
    try {
      await c.env.DB.prepare(`
        INSERT INTO leads (id, zalo_user_id, name, phone, interest_area, interest_price, intent, last_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(zalo_user_id) DO UPDATE SET
          name = COALESCE(excluded.name, name),
          phone = COALESCE(excluded.phone, phone),
          interest_area = COALESCE(excluded.interest_area, interest_area),
          interest_price = COALESCE(excluded.interest_price, interest_price),
          intent = COALESCE(excluded.intent, intent),
          last_message = excluded.last_message
      `)
      .bind(
        uuid,
        zaloUserId,
        lead.name,
        lead.phone,
        lead.area,
        lead.price,
        lead.intent,
        text
      )
      .run();
    } catch (dbError) {
      console.error('Database insertion error:', dbError);
      return c.json({ 
        status: 'error', 
        message: 'Database persistence failed', 
        parsedLead: lead 
      }, 500);
    }

    return c.json({
      status: 'success',
      processed: true,
      parsedLead: lead
    });
  }

  return c.json({
    status: 'success',
    processed: false,
    message: `Event '${payload.event_name}' received and verified, but ignored.`
  });
});

export default app;
