import { Env, Lead } from './types';

/**
 * Fallback parser using regex and simple rules if the LLM fails or is unavailable.
 */
export function regexFallbackParser(text: string): Lead {
  // Matches Vietnamese phone numbers: starts with 03, 05, 07, 08, 09 followed by 8 digits
  const phoneRegex = /\b(0[35789]\d{8})\b/;
  const phoneMatch = text.match(phoneRegex);
  const phone = phoneMatch ? phoneMatch[1] : null;

  // Crude intent heuristic
  let intent: Lead['intent'] = 'cold';
  const lowerText = text.toLowerCase();
  
  if (
    lowerText.includes('mua') || 
    lowerText.includes('thuê') || 
    lowerText.includes('bán') || 
    lowerText.includes('tư vấn') ||
    lowerText.includes('sđt') ||
    phone
  ) {
    intent = 'warm';
  } else if (
    lowerText.includes('hello') || 
    lowerText.includes('hi') || 
    lowerText.includes('chào') && lowerText.length < 10
  ) {
    intent = 'cold';
  } else if (
    lowerText.includes('quảng cáo') || 
    lowerText.includes('rác') || 
    lowerText.includes('spam')
  ) {
    intent = 'junk';
  }

  return {
    name: null,
    phone,
    area: null,
    price: null,
    intent
  };
}

/**
 * Extracts structured lead variables from incoming message text using Cloudflare Workers AI.
 */
export async function parseLead(env: Env, text: string): Promise<Lead> {
  // If AI binding is missing, use fallback immediately
  if (!env.AI || typeof env.AI.run !== 'function') {
    console.warn('Workers AI binding not found, using regex fallback parser.');
    return regexFallbackParser(text);
  }

  const systemInstruction = `You are a Vietnamese real estate lead extraction bot.
Extract structured variables from user messages. Return details ONLY as a valid JSON object matching this schema:
{
  "name": string or null,
  "phone": string or null,
  "area": string or null,
  "price": string or null,
  "intent": "warm" | "cold" | "junk" or null
}

Rules:
1. "intent" classifications:
   - "warm": User expresses interest in buying/renting/selling, asks for advice, or leaves a phone number.
   - "cold": User says greeting or generic statement without clear action intent.
   - "junk": Advertising, spam, or gibberish.
2. If name, phone, area, or price cannot be identified, return null.
3. Clean phone numbers to digits.`;

  try {
    const model = '@cf/meta/llama-3-8b-instruct';
    const response = await env.AI.run(model, {
      messages: [
        { role: 'system', content: systemInstruction },
        { role: 'user', content: text }
      ],
      response_format: { type: 'json_object' }
    });

    if (!response || !response.response) {
      throw new Error('Empty response from Workers AI');
    }

    const lead = JSON.parse(response.response) as Lead;
    
    // Validate schema keys are present
    return {
      name: typeof lead.name === 'string' ? lead.name : null,
      phone: typeof lead.phone === 'string' ? lead.phone : (regexFallbackParser(text).phone),
      area: typeof lead.area === 'string' ? lead.area : null,
      price: typeof lead.price === 'string' ? lead.price : null,
      intent: ['warm', 'cold', 'junk'].includes(lead.intent as string) ? lead.intent : 'cold'
    };
  } catch (error) {
    console.error('LLM Lead parsing failed, falling back to regex parser. Error:', error);
    return regexFallbackParser(text);
  }
}
