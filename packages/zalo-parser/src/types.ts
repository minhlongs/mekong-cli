export interface Env {
  DB: D1Database;
  ZALO_OA_SECRET_KEY: string;
  AI: {
    run: (model: string, inputs: Record<string, unknown>) => Promise<{ response: string }>;
  };
}

export interface ZaloWebhookPayload {
  app_id: string;
  sender: {
    id: string;
  };
  recipient: {
    id: string;
  };
  event_name: string;
  message?: {
    text: string;
    msg_id: string;
  };
  timestamp: string;
}

export interface Lead {
  name: string | null;
  phone: string | null;
  area: string | null;
  price: string | null;
  intent: 'warm' | 'cold' | 'junk' | null;
}
