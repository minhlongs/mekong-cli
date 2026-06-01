# Nhịp Điệu Xanh CRM & Payment Integration Analysis

## 1. SePay Webhook Endpoint (POST /api/payments/sepay)

### 1.1 Signature Verification
To verify webhook notifications from SePay:
1. **Header Parsing**: The webhook will send a signature in either `x-sepay-signature` or `sepay-signature` headers.
2. **Raw Body Reading**: Next.js App Router route handlers must read the request body as raw text (`await req.text()`) rather than parsed JSON. Comparing signature hashes against formatted JSON can lead to validation failures due to spacing or key ordering differences.
3. **Bypass Checks**: If the environment variable `SEPAY_WEBHOOK_SECRET` is not set or set to `insecure_dev`, the webhook signature check is bypassed for easy testing and local development.
4. **HMAC Calculation**: We calculate the HMAC-SHA256 signature on the raw request text using the secret key, then compare it using `crypto.timingSafeEqual` to protect against timing attacks.

### 1.2 Memo Parsing & Robust Lead ID Formatting
The transfer description will be parsed from the webhook payload's `content` field.
* **Regex Extraction**: We extract the ID matching the pattern: `/NDX([0-9a-f]{8}-?[0-9a-f]{4}-?-?[0-9a-f]{4}-?-?[0-9a-f]{4}-?-?[0-9a-f]{12})/i`.
* **UUID Formatting Utility**: Customers or payment gateways might strip hyphens from the UUID (resulting in a 32-character string). To look up the lead correctly using Prisma's default `uuid()` fields, we format it back to the standard hyphenated 8-4-4-4-12 pattern:
  ```typescript
  function formatToUUID(idStr: string): string {
    const clean = idStr.replace(/[^0-9a-f]/gi, '').toLowerCase();
    if (clean.length === 32) {
      return `${clean.substring(0, 8)}-${clean.substring(8, 12)}-${clean.substring(12, 16)}-${clean.substring(16, 20)}-${clean.substring(20)}`;
    }
    return idStr;
  }
  ```

### 1.3 Database & Event Updates
Upon valid verification and matching:
* Query the database to ensure the lead exists: `prisma.lead.findUnique(...)`. If not found, return `404 Not Found`.
* Update the lead's status to `'won'`.
* Trigger `publishLeadEvent` (to Kafka) with the updated status. This maintains consistency with the lead lifecycle.

### 1.4 Webhook Implementation Design

```typescript
// apps/nhipdieuxanh/app/api/payments/sepay/route.ts
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import crypto from 'crypto'
import { publishLeadEvent } from '@/lib/kafka'

function formatToUUID(idStr: string): string {
  const clean = idStr.replace(/[^0-9a-f]/gi, '').toLowerCase()
  if (clean.length === 32) {
    return `${clean.substring(0, 8)}-${clean.substring(8, 12)}-${clean.substring(12, 16)}-${clean.substring(16, 20)}-${clean.substring(20)}`
  }
  return idStr
}

export async function POST(req: Request) {
  try {
    const rawBody = await req.text()
    const signatureHeader = req.headers.get('x-sepay-signature') || req.headers.get('sepay-signature')
    const secret = process.env.SEPAY_WEBHOOK_SECRET

    // Signature Verification
    if (secret && secret !== 'insecure_dev') {
      if (!signatureHeader) {
        return NextResponse.json({ error: 'missing_signature', message: 'Signature header is missing' }, { status: 401 })
      }
      
      const computedSignature = crypto
        .createHmac('sha256', secret)
        .update(rawBody)
        .digest('hex')

      try {
        const sigBuffer = Buffer.from(signatureHeader, 'hex')
        const compBuffer = Buffer.from(computedSignature, 'hex')
        
        if (sigBuffer.length !== compBuffer.length || !crypto.timingSafeEqual(sigBuffer, compBuffer)) {
          return NextResponse.json({ error: 'invalid_signature', message: 'Signature verification failed' }, { status: 401 })
        }
      } catch (err) {
        return NextResponse.json({ error: 'invalid_signature', message: 'Signature verification failed' }, { status: 401 })
      }
    }

    const payload = JSON.parse(rawBody)
    const memo = payload.content || ''
    
    // Parse Lead ID using regular expression
    const ndxRegex = /NDX([0-9a-f]{8}-?[0-9a-f]{4}-?-?[0-9a-f]{4}-?-?[0-9a-f]{4}-?-?[0-9a-f]{12})/i
    const match = memo.match(ndxRegex)
    
    if (!match) {
      return NextResponse.json({ 
        error: 'lead_id_not_found', 
        message: 'Could not parse Lead ID from transfer content' 
      }, { status: 400 })
    }

    const rawLeadId = match[1]
    const leadId = formatToUUID(rawLeadId)

    // Verify Lead existence
    const existingLead = await prisma.lead.findUnique({
      where: { id: leadId }
    })

    if (!existingLead) {
      return NextResponse.json({ 
        error: 'lead_not_found', 
        message: `Lead with ID ${leadId} not found` 
      }, { status: 404 })
    }

    // Update status to 'won'
    const updatedLead = await prisma.lead.update({
      where: { id: leadId },
      data: { status: 'won' }
    })

    // Publish event to Kafka
    publishLeadEvent({
      id: updatedLead.id,
      name: updatedLead.name,
      phone: updatedLead.phone,
      email: updatedLead.email,
      need: updatedLead.need,
      budget: updatedLead.budget,
      area: updatedLead.area,
      status: updatedLead.status,
      level: updatedLead.level,
      consent: true,
      source: updatedLead.source
    }).catch(err => console.error('[SePay Webhook] Kafka publish event failed:', err))

    return NextResponse.json({
      success: true,
      message: `Lead status updated to 'won' for lead ID: ${leadId}`,
      lead: { id: updatedLead.id, status: updatedLead.status }
    }, { status: 200 })

  } catch (error: unknown) {
    const errMsg = error instanceof Error ? error.message : String(error)
    console.error('[POST /api/payments/sepay] Error:', errMsg)
    return NextResponse.json({ error: 'server_error', message: 'Internal server error' }, { status: 500 })
  }
}
```

---

## 2. Booking Modal on Landing Page

### 2.1 UI Flow Integration
* After the lead forms is successfully submitted, instead of a static message, show an options screen:
  1. A primary **"Đặt Cọc Giữ Chỗ Ngay" (Deposit 10M to Book)** button.
  2. A secondary **"Đăng ký nhu cầu mới" (Register new demand)** button.
* When clicked, "Đặt Cọc Giữ Chỗ Ngay" launches a Booking Modal.

### 2.2 Dynamic VietQR Generation
Using the `img.vietqr.io` API, generate a QR image:
* Bank Account Info is configurable via environment variables (`NEXT_PUBLIC_BANK_ID`, `NEXT_PUBLIC_BANK_ACCOUNT`, `NEXT_PUBLIC_BANK_ACCOUNT_NAME`).
* **URL Syntax**:
  `https://img.vietqr.io/image/${bankId}-${accountNo}-compact.png?amount=10000000&addInfo=NDX${leadId}&accountName=${encodeURIComponent(accountName)}`

### 2.3 Status Polling and React Design
To check payment status dynamically, the frontend polls the lead status endpoint.
* **Polling Endpoint**: Design a dynamic route `apps/nhipdieuxanh/app/api/leads/[id]/status/route.ts` which returns `{ success: true, status: string }`.
* **Important Next.js 16 Detail**: In Next.js 16, `params` in dynamic routes is a `Promise` and must be awaited:
  ```typescript
  export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const lead = await prisma.lead.findUnique({
      where: { id },
      select: { status: true }
    });
    ...
  }
  ```
* **React Polling Hook**:
  - The modal uses a `setInterval` to fetch lead status every 3 seconds.
  - Clears interval immediately once status becomes `'won'`.
  - Clears interval on unmount or modal close to prevent memory leaks.
  - Implements a 10-minute timeout limit to avoid indefinite polling.

---

## 3. Landing Page Emerald Green Upgrade

### 3.1 Animations
Premium interactive elements:
* **Fade-in-up animations**: On hero elements and section headings.
* **Hover transforms**: Scale buttons up (`hover:scale-[1.02] active:scale-[0.98] duration-300`).
* **Loading Spinners**: For form submission, VietQR loading skeleton, and payment verification states.

### 3.2 Touch Targets (>= 44px)
Audit of existing interactive targets:
* Header CTA "Liên Hệ Ngay": Upgrade padding to `px-6 py-3.5` to ensure height is >= 44px on all viewports.
* Inputs: Ensure `py-3` is used (equal to 44px height).
* Select menus: Standardize heights to match inputs.
* Close buttons and links: Add `min-w-[44px] min-h-[44px]` touch target sizing.

### 3.3 Form Loading States
Enhance form behavior:
* Disable all inputs (`disabled={loading}`) during form processing to prevent double submission.
* Disable select menus and buttons during ingest operations.

### 3.4 Mobile Layout & Responsiveness
To avoid horizontal scroll at 375px:
* Use Tailwind's grid structure properly. Hero columns should wrap to a single column (`grid lg:grid-cols-12`).
* Ensure elements with absolute positioning (such as blur blobs) use `overflow-hidden` container limits to prevent horizontal layout leakage.
* Wrap the header using `flex-wrap` and scale logo text down on smaller devices to avoid squeezing or clipping contents.

---

## 4. Operations Guide Structure
The `docs/nhipdieuxanh_operations.md` file has been drafted and saved in the workspace. It covers:
1. Operational Architecture & Webhook Flows
2. Environment Configuration
3. Webhook Setup Instructions
4. Testing and Mocking Playbooks (verifying HMAC validation bypass or active keys)
5. Troubleshooting common payment matching and Kafka connection issues.
