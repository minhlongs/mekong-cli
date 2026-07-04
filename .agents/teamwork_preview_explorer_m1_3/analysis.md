# Nhịp Điệu Xanh CRM: Payment Integration & UX Upgrade Analysis

This report provides a detailed design analysis for the Nhịp Điệu Xanh AI CRM platform. It outlines the specifications for integrating the SePay VietQR payment webhook, building the responsive Booking Modal with dynamic VietQR generation and status polling, upgrading the landing page design with the Emerald Green theme, and structuring the system operations guide.

---

## 1. SePay Webhook Endpoint (`POST /api/payments/sepay`)

The SePay webhook endpoint acts as the automated payment confirmation gateway. When a user completes a bank transfer via VietQR, SePay sends a POST request with the transaction details.

### A. Endpoint Specifications & Route Location
* **Route Path:** `apps/nhipdieuxanh/app/api/payments/sepay/route.ts`
* **HTTP Method:** `POST`
* **Content-Type:** `application/json`

### B. Payload Structure (Contract)
The payload sent by SePay will conform to the following fields:
```json
{
  "id": 1234567,
  "gateway": "MBBank",
  "transferAmount": 10000000,
  "content": "NDXf834d852-7e04-4530-9b3f-141680d287fa",
  "transferType": "in",
  "transactionDate": "2026-05-30 06:00:00"
}
```

### C. Signature Verification Logic (HMAC-SHA256)
1. **Header Verification:** SePay sends the HMAC signature in either the `x-sepay-signature` or `sepay-signature` HTTP header.
2. **Payload Hashing:** The signature is calculated by hashing the raw, unparsed request text body using the secret key configured in the environment:
   $$\text{Signature} = \text{HMAC-SHA256}(\text{rawBody}, \text{secret})$$
3. **Bypass Option:** If the `SEPAY_WEBHOOK_SECRET` environment variable is not configured or is explicitly set to `'insecure_dev'`, the endpoint will skip signature verification and log a warning. This is crucial for local testing and development.
4. **Timing Attack Protection:** When verifying, use `crypto.timingSafeEqual` or compare hex values securely to prevent timing side-channel attacks.

### D. Memo Content Parsing
* **Pattern:** The memo `content` must contain `NDX<leadId>`, where `<leadId>` is a 36-character UUID v4 identifier.
* **Extraction:** Use a regular expression to match and extract the UUID.
  ```typescript
  const match = content.match(/NDX([a-fA-F0-9\-]{36})/i);
  ```
* **Validation:** If the lead ID is found, query the database. If not, return a `200 OK` status with a descriptive log message (preventing infinite retry cycles from the bank gateway for invalid client inputs).

### E. Database Status Update
* **ORM:** Prisma Client pointing to the PostgreSQL database.
* **Target State:** Set the `status` field of the matching `Lead` record to `'won'`.
* **Idempotency:** If the lead status is already `'won'`, return `200 OK` immediately with a success message to handle retries without double-processing.

### F. Proposed Route Handler Implementation
```typescript
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import crypto from 'crypto'

export async function POST(req: Request) {
  try {
    const signatureHeader = req.headers.get('x-sepay-signature') || req.headers.get('sepay-signature')
    const rawBody = await req.text()
    
    const secret = process.env.SEPAY_WEBHOOK_SECRET
    const shouldBypass = !secret || secret === 'insecure_dev'

    // 1. Signature Verification
    if (!shouldBypass) {
      if (!signatureHeader) {
        return NextResponse.json(
          { error: 'unauthorized', message: 'Signature header is missing' },
          { status: 401 }
        )
      }
      
      const computedSignature = crypto
        .createHmac('sha256', secret)
        .update(rawBody)
        .digest('hex')
        
      // Timing-safe comparison
      const sigBuffer = Buffer.from(signatureHeader, 'hex')
      const compBuffer = Buffer.from(computedSignature, 'hex')
      if (sigBuffer.length !== compBuffer.length || !crypto.timingSafeEqual(sigBuffer, compBuffer)) {
        return NextResponse.json(
          { error: 'unauthorized', message: 'Invalid signature' },
          { status: 401 }
        )
      }
    } else {
      console.warn('[SePay Webhook] Bypassing HMAC verification in development mode.')
    }

    // 2. Parse Payload
    const payload = JSON.parse(rawBody)
    const { content, transferType, transferAmount, id: transactionId } = payload

    // 3. Direction Check
    if (transferType !== 'in') {
      return NextResponse.json(
        { success: true, message: 'Ignored non-incoming transaction direction' },
        { status: 200 }
      )
    }

    // 4. Parse Memo to Extract Lead ID
    // Supports NDX followed by 36-char UUID (case-insensitive)
    const match = content?.match(/NDX([a-fA-F0-9\-]{36})/i)
    if (!match) {
      console.warn(`[SePay Webhook] Unparseable memo format: "${content}" in transaction ID: ${transactionId}`)
      return NextResponse.json(
        { success: true, message: 'Memo format not recognized. Manual review required.' },
        { status: 200 }
      )
    }

    const leadId = match[1]

    // 5. Database Transaction Status Update
    const lead = await prisma.lead.findUnique({
      where: { id: leadId }
    })

    if (!lead) {
      console.error(`[SePay Webhook] Lead ID "${leadId}" from transaction ${transactionId} not found in database.`)
      return NextResponse.json(
        { success: true, message: 'Lead record not found. Manual review required.' },
        { status: 200 }
      )
    }

    // Idempotence check
    if (lead.status === 'won') {
      return NextResponse.json(
        { success: true, message: `Lead ${leadId} was already marked as won.` },
        { status: 200 }
      )
    }

    // Update status to 'won'
    await prisma.lead.update({
      where: { id: leadId },
      data: { status: 'won' }
    })

    console.info(`[SePay Webhook] Successfully processed transaction ${transactionId}. Lead ${leadId} status set to 'won'.`)
    return NextResponse.json(
      { success: true, message: `Successfully updated status for lead ${leadId} to 'won'.` },
      { status: 200 }
    )

  } catch (error: any) {
    console.error('[SePay Webhook] Unexpected runtime error:', error)
    return NextResponse.json(
      { error: 'server_error', message: 'An internal error occurred while processing the webhook.' },
      { status: 500 }
    )
  }
}
```

---

## 2. Booking Modal on Landing Page

The Booking Modal offers immediate booking options to registered leads. Instead of showing a static success banner, the page opens a modal that guides the user to complete their deposit via VietQR.

### A. Dynamic VietQR Generation
We construct the QR code source dynamically using the standard API at `img.vietqr.io`.
* **API Pattern:** `https://img.vietqr.io/image/<BANK_ID>-<ACCOUNT_NO>-compact2.png?amount=<AMOUNT>&addInfo=<MEMO>&accountName=<ACCOUNT_NAME>`
* **Parameters:**
  * `BANK_ID`: The recipient bank code, e.g., `MB` (Military Bank).
  * `ACCOUNT_NO`: The bank account number.
  * `TEMPLATE`: `compact2` (renders a clean QR with transaction details embedded).
  * `amount`: `10000000` (10,000,000 VND).
  * `addInfo`: The custom memo `NDX<leadId>` (e.g. `NDXf834d852-7e04-4530-9b3f-141680d287fa`).
  * `accountName`: The bank account owner name (URL-encoded).

### B. Polling & Status Checking Endpoint
We need a lightweight status query endpoint that returns the lead's current status:
* **Location:** `apps/nhipdieuxanh/app/api/leads/status/route.ts`
* **HTTP Method:** `GET`
* **Query Parameters:** `id=<leadId>`
* **Response:** `{ success: true, status: 'new' | 'won' | ... }`

```typescript
// Proposed Implementation in apps/nhipdieuxanh/app/api/leads/status/route.ts
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json(
        { error: 'missing_id', message: 'Parameter "id" is required.' },
        { status: 400 }
      )
    }

    const lead = await prisma.lead.findUnique({
      where: { id },
      select: { status: true }
    })

    if (!lead) {
      return NextResponse.json(
        { error: 'not_found', message: 'Lead not found.' },
        { status: 404 }
      )
    }

    return NextResponse.json({ success: true, status: lead.status })
  } catch (error: any) {
    return NextResponse.json(
      { error: 'server_error', message: error.message },
      { status: 500 }
    )
  }
}
```

### C. Booking Modal Component Design & Polling Loop
* **Interval:** The modal checks the status every 3000ms.
* **Duration:** Polling times out after 10 minutes. Upon timeout, the modal displays support hotline information.
* **UX Copy Functions:** Interactive "Copy" buttons for account details, transfer amount, and memo to reduce typos.
* **Manual Verification:** A button "Tôi đã chuyển khoản" allows the user to force an immediate status check.

#### Proposed Frontend Integration code (React Hook / UI Layout)
```tsx
import React, { useState, useEffect, useRef } from 'react'
import { CheckCircle2, Copy, AlertTriangle, HelpCircle, Loader2 } from 'lucide-react'

interface BookingModalProps {
  isOpen: boolean
  onClose: () => void
  leadId: string
}

export default function BookingModal({ isOpen, onClose, leadId }: BookingModalProps) {
  const [status, setStatus] = useState<'pending' | 'checking' | 'won' | 'timeout' | 'error'>('pending')
  const [timeRemaining, setTimeRemaining] = useState(600) // 10 minutes count down
  const [copiedField, setCopiedField] = useState<string | null>(null)
  
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const bankId = process.env.NEXT_PUBLIC_BANK_ID || 'MB'
  const accountNo = process.env.NEXT_PUBLIC_BANK_ACCOUNT || '123456789'
  const accountOwner = process.env.NEXT_PUBLIC_BANK_ACCOUNT_NAME || 'NHIP DIEU XANH CRM'
  const amount = 10000000
  const memo = `NDX${leadId}`
  
  const qrCodeUrl = `https://img.vietqr.io/image/${bankId}-${accountNo}-compact2.png?amount=${amount}&addInfo=${memo}&accountName=${encodeURIComponent(accountOwner)}`

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  // Fetch lead status from API
  const checkPaymentStatus = async (isManual = false) => {
    if (isManual) setStatus('checking')
    try {
      const res = await fetch(`/api/leads/status?id=${leadId}`)
      const data = await res.json()
      if (res.ok && data.status === 'won') {
        setStatus('won')
        // Clean up intervals
        cleanup()
      } else if (isManual) {
        // If manual check did not find 'won' status
        setStatus('pending')
      }
    } catch (err) {
      console.error('Error fetching lead status:', err)
      if (isManual) setStatus('error')
    }
  }

  const cleanup = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
  }

  useEffect(() => {
    if (isOpen && leadId) {
      setStatus('pending')
      setTimeRemaining(600)

      // Start countdown timer
      timerRef.current = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            cleanup()
            setStatus('timeout')
            return 0
          }
          return prev - 1
        })
      }, 1000)

      // Start status polling
      pollIntervalRef.current = setInterval(() => {
        checkPaymentStatus()
      }, 3000)
    }

    return () => cleanup()
  }, [isOpen, leadId])

  if (!isOpen) return null

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div 
        className="w-full max-w-lg bg-white rounded-3xl border border-slate-200 shadow-2xl overflow-hidden transition-all transform scale-100 animate-fade-in"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="bg-emerald-50 border-b border-emerald-100 p-6 flex justify-between items-center">
          <div>
            <h3 className="text-lg font-bold text-emerald-950">Đặt Cọc & Nhận Đặc Quyền VIP</h3>
            <p className="text-xs text-emerald-700">Mã cọc giữ chỗ nền sinh thái sinh lời</p>
          </div>
          <button 
            onClick={onClose} 
            className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-emerald-100 text-emerald-950 font-bold transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6">
          {status === 'won' ? (
            <div className="text-center py-8 space-y-4">
              <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner animate-bounce">
                <CheckCircle2 className="w-12 h-12" />
              </div>
              <h4 className="text-xl font-bold text-slate-900">Thanh Toán Thành Công!</h4>
              <p className="text-sm text-slate-500 max-w-sm mx-auto">
                Hệ thống đã ghi nhận khoản cọc **10.000.000 VNĐ** của quý khách. Chuyên viên sẽ liên hệ và gửi hợp đồng xác nhận cọc giữ chỗ ngay lập tức.
              </p>
              <button 
                onClick={onClose}
                className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-lg transition-colors cursor-pointer text-sm"
              >
                Hoàn tất
              </button>
            </div>
          ) : status === 'timeout' ? (
            <div className="text-center py-8 space-y-4">
              <div className="w-20 h-20 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto">
                <AlertTriangle className="w-12 h-12" />
              </div>
              <h4 className="text-xl font-bold text-slate-900">Hết Thời Gian Chờ</h4>
              <p className="text-sm text-slate-500 max-w-sm mx-auto">
                Phiên giao dịch tự động đã hết hiệu lực. Nếu quý khách đã chuyển khoản, vui lòng liên hệ hotline bộ phận kế toán để xác thực thủ công.
              </p>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs text-left">
                <p className="font-semibold text-slate-800">Hotline hỗ trợ:</p>
                <p className="text-emerald-700 font-bold mt-0.5">1800-xxxx (Miễn phí) hoặc 09xx-xxx-xxx</p>
              </div>
              <div className="flex space-x-3">
                <button 
                  onClick={() => checkPaymentStatus(true)}
                  className="flex-1 py-3 border border-slate-200 hover:border-emerald-600 text-slate-700 font-medium rounded-xl text-sm transition-colors cursor-pointer"
                >
                  Kiểm tra lại
                </button>
                <button 
                  onClick={onClose}
                  className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium rounded-xl text-sm transition-colors cursor-pointer"
                >
                  Đóng
                </button>
              </div>
            </div>
          ) : (
            <div className="grid md:grid-cols-12 gap-6 items-center">
              {/* Left Column: QR Code */}
              <div className="md:col-span-5 text-center space-y-3">
                <div className="border border-slate-200 rounded-2xl p-2 bg-slate-50 shadow-inner inline-block">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img 
                    src={qrCodeUrl} 
                    alt="VietQR Payment Transfer Code" 
                    className="w-40 h-40 object-contain mx-auto"
                  />
                </div>
                <div className="text-center space-y-1">
                  <span className="block text-xs font-bold text-slate-500">Quét mã bằng ứng dụng Ngân hàng</span>
                  <span className="inline-flex items-center space-x-1 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-700 rounded-full text-xs font-bold">
                    <span>Hiệu lực còn: {formatTime(timeRemaining)}</span>
                  </span>
                </div>
              </div>

              {/* Right Column: Transfer Info */}
              <div className="md:col-span-7 space-y-3.5">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                    <span className="text-slate-500 font-medium">Ngân hàng thụ hưởng:</span>
                    <span className="font-bold text-slate-800">MB Bank (Quân Đội)</span>
                  </div>
                  
                  <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                    <span className="text-slate-500 font-medium">Số tài khoản:</span>
                    <div className="flex items-center space-x-1">
                      <span className="font-bold text-slate-800">{accountNo}</span>
                      <button 
                        onClick={() => handleCopy(accountNo, 'acc')}
                        className="p-1 hover:bg-slate-100 rounded text-slate-500 transition-colors cursor-pointer"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                    <span className="text-slate-500 font-medium">Chủ tài khoản:</span>
                    <span className="font-bold text-slate-800">{accountOwner}</span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                    <span className="text-slate-500 font-medium">Số tiền cọc:</span>
                    <div className="flex items-center space-x-1">
                      <span className="font-extrabold text-emerald-600 text-sm">10.000.000 VND</span>
                      <button 
                        onClick={() => handleCopy('10000000', 'amount')}
                        className="p-1 hover:bg-slate-100 rounded text-slate-500 transition-colors cursor-pointer"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-between items-center pb-1">
                    <span className="text-slate-500 font-medium">Nội dung chuyển khoản (Memo):</span>
                    <div className="flex items-center space-x-1">
                      <span className="font-bold text-amber-600 bg-amber-50 px-2 py-0.5 border border-amber-200 rounded">{memo}</span>
                      <button 
                        onClick={() => handleCopy(memo, 'memo')}
                        className="p-1 hover:bg-slate-100 rounded text-slate-500 transition-colors cursor-pointer"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200/50 rounded-xl p-3 flex items-start space-x-2">
                  <AlertTriangle className="w-4.5 h-4.5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span className="text-[10px] text-amber-800 leading-normal font-medium">
                    **Quan trọng:** Vui lòng giữ nguyên nội dung chuyển khoản **{memo}** để hệ thống duyệt cọc tự động trong 30 giây.
                  </span>
                </div>

                {copiedField && (
                  <div className="text-center text-xs font-bold text-emerald-600 bg-emerald-50 py-1.5 rounded-lg border border-emerald-200 animate-pulse">
                    ✓ Đã sao chép thông tin {copiedField === 'acc' ? 'Số tài khoản' : copiedField === 'amount' ? 'Số tiền' : 'Nội dung chuyển khoản'}!
                  </div>
                )}

                <button 
                  onClick={() => checkPaymentStatus(true)}
                  disabled={status === 'checking'}
                  className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-300 text-white font-bold rounded-xl shadow-lg transition-colors cursor-pointer text-xs uppercase tracking-wider flex items-center justify-center space-x-1.5"
                >
                  {status === 'checking' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Đang kiểm tra giao dịch...</span>
                    </>
                  ) : (
                    <span>Tôi đã chuyển khoản</span>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

---

## 3. Landing Page Emerald Green Upgrade

Upgrading the user interface parameters on the landing page is key to improving user conversion rates. The branding and aesthetic will align with **Google Material Design 3 (M3) Adaptive** guidelines under the **Emerald Green** paradigm.

### A. Emerald Theme Colors & Custom Styles
Tailwind v4 theme extensions in `globals.css` can be enhanced to expose semantic design tokens:
* `--background`: `#ffffff` (light background) / `#060b13` (dark mode)
* `--primary`: `#10b981` (Emerald-500)
* `--primary-hover`: `#059669` (Emerald-600)
* `--accent`: `#10b981` (standard color accent)
* `--muted-emerald`: `#e6fcf5` (very soft mint color for banner backs and cards)

### B. Micro-Animations and Motion Spec
1. **Interactive Buttons:** Add smooth scaling and transition timings to interactive layers:
   - `transition-all duration-200 ease-in-out hover:scale-[1.02] active:scale-[0.98] focus:ring-4 focus:ring-emerald-500/20`
2. **Modal Fade & Scale:** Ensure standard keyframes are loaded:
   - Backdrop opacity transition: `opacity-0` to `opacity-100`.
   - Card animation: `scale-95 translate-y-2 opacity-0` to `scale-100 translate-y-0 opacity-100` via Tailwind classes `animate-fade-in` and transition timing curves (`cubic-bezier(0.34, 1.56, 0.64, 1)`).
3. **Spinner Loaders:** Simple React CSS spinner for submitting forms.

### C. Touch-Target Optimization (Accessibility compliance WCAG 2.1 AA)
* **Rule:** All interactive controls (buttons, links, inputs) must occupy a minimum visual height/width of **44px** (with recommendation to hit 48px).
* **Implementation details:**
  - Standardize all navigation and CTA buttons: replace `py-2` (which yields ~36-40px depending on line height) with `py-3` or `py-3.5` (yielding 46px or 48px).
  - Form selects and input fields: ensure standard layout elements are configured with `h-12` or `py-3` padding.
  - Social media/small links: use inline-flex with `min-h-[44px] min-w-[44px]` wrap blocks.

### D. Mobile Responsiveness / 375px Verification
To prevent horizontal scrolling on small mobile viewports (e.g. iPhone SE at 375px):
1. **Wrapper Control:** Set `overflow-x-hidden` on the main page canvas container.
2. **Grid Layouts:** Ensure layout grids utilize `grid-cols-1 md:grid-cols-2 lg:grid-cols-12` rather than forcing horizontal rows.
3. **Flexible Padding:** Use responsive padding units (e.g. `px-4 sm:px-6 lg:px-8`) instead of rigid margins.
4. **Responsive Sizing:** Use relative font heights (e.g. `text-3xl sm:text-5xl`) and relative sizing for absolute layout elements.

---

## 4. Operations Guide Structure (`docs/nhipdieuxanh_operations.md`)

Below is the designed blueprint for the operations guide, which acts as the core documentation index for maintenance and administration.

```markdown
# Nhịp Điệu Xanh AI CRM — Operations & Management Guide

## 1. System Overview & Architecture
* High-Level Architectural Flow (Web/Landing Page -> NextJS Router -> PostgreSQL/Prisma).
* External Service Integrations (Kafka event streaming, Sepay bank gateway callback, blockchain notarization).
* Data Pipeline Diagrams (lead lifecycle from ingestion to 'won' status conversion).

## 2. Environment Setup & Configuration
* Complete list of required `.env` variables and parameters.
* Database connections (PostgreSQL details, local Docker container instructions, and schema migration keys).
* Configuring SePay Webhook parameters (`SEPAY_API_KEY`, `SEPAY_WEBHOOK_SECRET`).
* Custom brand identifiers (`NEXT_PUBLIC_BANK_ID`, `NEXT_PUBLIC_BANK_ACCOUNT`, `NEXT_PUBLIC_BANK_ACCOUNT_NAME`).

## 3. Lead Ingestion, Scoring & Privacy Rules
* Dynamic Lead Scoring Formula (scoring weights for phone validity, location, intent, and budget tiers).
* Decree 13/2023/NĐ-CP Privacy Boundary compliance.
* Lead Masking and Secure PII Hash Generation rules (PII regex redactors for names, phones, emails).

## 4. SePay Webhook & Payment Verification
* Webhook Callback Payload Specification (Contract).
* HMAC-SHA256 signature verification sequence (generating secret keys, header mapping).
* Bypass protocols for Local Development and Staged Testing ('insecure_dev' fallback).
* Memo format parsing rules (`NDX<leadId>` parsing regex).

## 5. Daily Operations & Troubleshooting Checklist
* Handling Unparseable Webhook Memos (Weekly log inspections).
* Resolving Duplicate or Double-counted Transactions (idempotency policy checks).
* Manual Reconciliation Workflow (steps for manually verifying transactions at the bank and overriding status via the database console).
* Diagnostic shell scripts and tail command recipes for log inspection.
```

---

## 5. Evidence Chain & Verification Methods

### A. Code Locations Inspected
1. **Database Schema:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/prisma/schema.prisma`
   - Confirmed `Lead` model contains `id: String` (UUID) and `status: String` (default `"new"`).
2. **Current API Ingestion Handler:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/app/api/leads/route.ts`
   - Verified that successful ingestion returns `{ success: true, leadId: lead.id }` which provides the necessary `leadId` to trigger the booking modal.
3. **Status Update Handler:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/app/api/leads/update-status/route.ts`
   - Confirmed `'won'` is a valid status code in `validStatuses = ['new', 'contacted', 'viewing', 'negotiation', 'won', 'prospecting']`.
4. **Current Landing Page Structure:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/app/page.tsx`
   - Confirmed current layout uses Tailwind v4 and Lucide-React icons.

### B. Suggested Testing & Verification Commands
Once implemented, the following test procedures can be executed:
1. **Mock SePay Webhook Test:**
   ```bash
   curl -i -X POST http://localhost:3000/api/payments/sepay \
     -H "Content-Type: application/json" \
     -H "x-sepay-signature: bypass_if_not_configured" \
     -d '{"id":"tx_123456","gateway":"MBBank","transferAmount":10000000,"content":"NDXf834d852-7e04-4530-9b3f-141680d287fa","transferType":"in"}'
   ```
2. **Prisma Status Check (PostgreSQL verification):**
   ```bash
   npx prisma db pull --schema=apps/nhipdieuxanh/prisma/schema.prisma
   # Or directly query the database table to verify the status column for the lead is set to 'won'.
   ```
3. **Visual layout test at 375px viewport:**
   Run `vitest` unit checks or use Playwright to simulate mobile viewports at 375px width, asserting that horizontal scroll does not trigger (`window.scrollX === 0`).
