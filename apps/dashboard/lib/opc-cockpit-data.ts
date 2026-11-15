export type SupportedCurrency = 'USD' | 'VND' | 'EUR'
export type SupportedLanguage = 'en' | 'vi'
export type VatRatePct = 0 | 5 | 8 | 10
export type TvanExportFormat = 'CSV' | 'XML' | 'JSON'
export type AccountingTargetProvider = 'misa_meinvoice' | 'sapo_invoice'
export type SmeQuotaTierKey = 'starter' | 'pilot_a' | 'growth' | 'agency'
export type SelectiveRoutingTierId = 'deterministic_python' | 'local_mlx' | 'cloud_fallback'

export const MIN_EXTRACTION_CONFIDENCE = 0.85
export const ZALO_FREE_WINDOW_HOURS = 48

export interface OpcActionPayload {
  attachments: string[]
  budget_amount: string
  budget_currency: SupportedCurrency
  capability: string
  connector: string
  content: string
  expires_at: number
  parameters: {
    amount: string
    project_title: string
  }
  principal: string
  recipient: string
}

export interface OpcLineItem {
  service: string
  hours: number
  rate: number
  subtotal: number
  isUnpriced: boolean
}

export type UsageStage = 'estimated' | 'reserved' | 'actual' | 'unknown'

export interface OpcUsageEvent {
  event_id: string
  run_id: string
  stage: UsageStage
  provider: string
  model: string
  tokens: number
  amount: string | null
  currency: SupportedCurrency
  pricing_source: string
  routing_tier?: SelectiveRoutingTierId
  event_code?: 'KNOWN_ZERO_COST' | 'KNOWN_METERED_COST' | 'UNKNOWN_COST_EVENT'
}

export interface ServiceCatalogEntry {
  labelEn: string
  labelVi: string
  rates: Record<SupportedCurrency, number | null>
  keywordsVi: string[]
  keywordsEn: string[]
}

export const SERVICE_CATALOG: Record<string, ServiceCatalogEntry> = {
  zalo_oa_lead_to_quote: {
    labelEn: 'Zalo OA Auto Lead-to-Quote Setup',
    labelVi: 'Thiết lập Báo giá Tự động Zalo OA',
    rates: { VND: 600000, USD: 24, EUR: 22 },
    keywordsVi: ['Zalo OA báo giá tự động', 'báo giá tự động', 'Zalo OA'],
    keywordsEn: ['Zalo OA auto quote', 'lead-to-quote', 'Zalo OA'],
  },
  vietqr_reconciliation_setup: {
    labelEn: 'VietQR Napas 247 Order Reconciliation',
    labelVi: 'Tích hợp Đối soát VietQR Napas 247',
    rates: { VND: 400000, USD: 16, EUR: 15 },
    keywordsVi: ['đối soát VietQR', 'VietQR Napas 247', 'VietQR'],
    keywordsEn: ['VietQR reconciliation', 'Napas 247', 'VietQR'],
  },
  misa_sapo_tvan_draft: {
    labelEn: 'MISA / Sapo Pre-Accounting Draft Bridge',
    labelVi: 'Kết nối Nháp Hóa đơn MISA / Sapo (TVAN)',
    rates: { VND: 350000, USD: 14, EUR: 13 },
    keywordsVi: ['xuất hóa đơn VAT', 'MISA', 'Sapo', 'hóa đơn'],
    keywordsEn: ['MISA', 'Sapo', 'VAT invoice draft'],
  },
  architecture_review: {
    labelEn: 'Architecture Review',
    labelVi: 'Thẩm định Kiến trúc Hệ thống',
    rates: { USD: 150, VND: 3750000, EUR: 140 },
    keywordsVi: ['thẩm định kiến trúc', 'kiến trúc hệ thống'],
    keywordsEn: ['architecture review', 'system architecture'],
  },
  cloud_migration_plan: {
    labelEn: 'Cloud Migration Plan',
    labelVi: 'Kế hoạch Dịch chuyển Cloud',
    rates: { USD: 180, VND: 4500000, EUR: 168 },
    keywordsVi: ['dịch chuyển cloud', 'hạ tầng cloud'],
    keywordsEn: ['cloud migration', 'cloud plan'],
  },
  security_audit: {
    labelEn: 'Security & Cryptography Audit',
    labelVi: 'Kiểm toán Bảo mật & Mật mã',
    rates: { USD: 200, VND: 5000000, EUR: 185 },
    keywordsVi: ['kiểm toán bảo mật', 'bảo mật'],
    keywordsEn: ['security audit', 'cryptography audit'],
  },
  custom_connector_bespoke: {
    labelEn: 'Bespoke External Connector (Unpriced / Unknown)',
    labelVi: 'Kết nối Hệ thống Riêng (Chưa có bảng giá / Unknown Cost)',
    rates: { USD: null, VND: null, EUR: null },
    keywordsVi: ['kết nối riêng', 'ERP riêng', 'tùy chỉnh riêng'],
    keywordsEn: ['bespoke connector', 'custom ERP'],
  },
}

export interface SourceSpanCitation {
  id: string
  fieldKey: string
  labelVi: string
  labelEn: string
  matchedText: string
  start: number
  end: number
  resolvedValue: string
}

export interface SmeWorkflowTierSpec {
  key: SmeQuotaTierKey
  nameVi: string
  nameEn: string
  monthlyQuota: number
  monthlyPriceVnd: number
  usedSample: number
}

export const VN_SME_WORKFLOW_TIERS: Record<SmeQuotaTierKey, SmeWorkflowTierSpec> = {
  starter: {
    key: 'starter',
    nameVi: 'Starter',
    nameEn: 'Starter',
    monthlyQuota: 300,
    monthlyPriceVnd: 790000,
    usedSample: 118,
  },
  pilot_a: {
    key: 'pilot_a',
    nameVi: 'Pilot A',
    nameEn: 'Pilot A',
    monthlyQuota: 500,
    monthlyPriceVnd: 990000,
    usedSample: 142,
  },
  growth: {
    key: 'growth',
    nameVi: 'Growth',
    nameEn: 'Growth',
    monthlyQuota: 1000,
    monthlyPriceVnd: 1990000,
    usedSample: 410,
  },
  agency: {
    key: 'agency',
    nameVi: 'Agency',
    nameEn: 'Agency',
    monthlyQuota: 3500,
    monthlyPriceVnd: 4900000,
    usedSample: 1280,
  },
}

export interface SelectiveRoutingStepInfo {
  id: SelectiveRoutingTierId
  titleVi: string
  titleEn: string
  costBadgeVi: string
  costBadgeEn: string
  slaNoteVi: string
  slaNoteEn: string
}

export const PROFILE_4_ROUTING_CHAIN: SelectiveRoutingStepInfo[] = [
  {
    id: 'deterministic_python',
    titleVi: 'Tất định Python 0đ',
    titleEn: 'Deterministic Python (0 VND)',
    costBadgeVi: '0 ₫ · Ưu tiên số 1',
    costBadgeEn: '0 VND · Primary',
    slaNoteVi: 'Tính tiền Decimal, kiểm tra cửa sổ 48h Zalo & tạo mã VietQR chuẩn xác 100%',
    slaNoteEn: 'Exact Decimal math, Zalo 48h window check & deterministic VietQR generation',
  },
  {
    id: 'local_mlx',
    titleVi: 'Local MLX',
    titleEn: 'Local MLX Inference',
    costBadgeVi: 'Nội bộ · 0 ₫ API ngoài',
    costBadgeEn: 'On-premise · 0 External API',
    slaNoteVi: 'Trích xuất source_span tiếng Việt sau khi ẩn danh SĐT/MST (SLA < 1500ms)',
    slaNoteEn: 'Extracts Vietnamese source_span after PII masking (< 1500ms failover)',
  },
  {
    id: 'cloud_fallback',
    titleVi: 'Cloud Fallback',
    titleEn: 'Cloud Fallback',
    costBadgeVi: 'Dự phòng tự động > 1500ms',
    costBadgeEn: 'Failover > 1500ms',
    slaNoteVi: 'Chỉ kích hoạt khi Local MLX quá hạn 1500ms và còn hạn mức ngân sách SQLite',
    slaNoteEn: 'Triggered only when Local MLX exceeds 1500ms with active SQLite budget lock',
  },
]

export interface QuoteFinancialSummary {
  subtotal: number
  vatRatePct: VatRatePct
  vatAmount: number
  grandTotal: number
  vietQrAmountVnd: number
  vietQrMemo: string
  vietQrEmvcoPreview: string
  vietQrAccountLabel: string
}

export function formatCurrencyAmount(amount: number, currency: SupportedCurrency): string {
  if (currency === 'VND') {
    return `${Math.round(amount).toLocaleString('vi-VN')} ₫`
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatActionAmountString(amount: number, currency: SupportedCurrency): string {
  if (currency === 'VND') {
    return String(Math.round(amount))
  }
  return (Math.round(amount * 100) / 100).toFixed(2)
}

/**
 * Minor-unit integer arithmetic so quote + VAT calculations never suffer IEEE-754 drift.
 */
export function computeQuoteFinancials(
  lineItems: OpcLineItem[],
  currency: SupportedCurrency,
  vatRatePct: VatRatePct,
  runId: string
): QuoteFinancialSummary {
  const scale = currency === 'VND' ? 1 : 100
  const subtotalMinor = lineItems.reduce((sum, item) => {
    if (item.isUnpriced) return sum
    return sum + Math.round(item.subtotal * scale)
  }, 0)
  const vatMinor = Math.round((subtotalMinor * vatRatePct) / 100)
  const grandTotalMinor = subtotalMinor + vatMinor

  const subtotal = subtotalMinor / scale
  const vatAmount = vatMinor / scale
  const grandTotal = grandTotalMinor / scale

  const vietQrAmountVnd =
    currency === 'VND'
      ? grandTotalMinor
      : currency === 'USD'
      ? Math.round(grandTotal * 25000)
      : Math.round(grandTotal * 27000)

  const sanitizedRun = runId.replace(/[^A-Za-z0-9_-]/g, '')
  const vietQrMemo = `OPC ${sanitizedRun}`
  const amountTag = String(vietQrAmountVnd)
  const vietQrEmvcoPreview = `00020101021238540010A0000007270124000697042201100988889999530370454${String(
    amountTag.length
  ).padStart(2, '0')}${amountTag}5802VN62${String(vietQrMemo.length + 4).padStart(
    2,
    '0'
  )}08${String(vietQrMemo.length).padStart(2, '0')}${vietQrMemo}6304A19F`

  return {
    subtotal,
    vatRatePct,
    vatAmount,
    grandTotal,
    vietQrAmountVnd,
    vietQrMemo,
    vietQrEmvcoPreview,
    vietQrAccountLabel: 'MB Bank (Napas 247) · STK 0988889999 · CTY TNHH MEKONG VIET',
  }
}

function findIgnoreCaseSpan(haystack: string, needle: string): { start: number; end: number } | null {
  if (!needle.trim()) return null
  const lowerHay = haystack.toLowerCase()
  const lowerNeedle = needle.toLowerCase()
  const idx = lowerHay.indexOf(lowerNeedle)
  if (idx === -1) return null
  return { start: idx, end: idx + needle.length }
}

export function extractSourceSpansFromMessage(
  message: string,
  services: string[],
  estimatedHours: number,
  vatRatePct: VatRatePct
): SourceSpanCitation[] {
  const citations: SourceSpanCitation[] = []

  for (const svcKey of services) {
    const entry = SERVICE_CATALOG[svcKey]
    if (!entry) continue
    const candidates = [...entry.keywordsVi, ...entry.keywordsEn]
    let matched: { start: number; end: number } | null = null
    for (const kw of candidates) {
      matched = findIgnoreCaseSpan(message, kw)
      if (matched) break
    }
    if (matched) {
      citations.push({
        id: `span_svc_${svcKey}`,
        fieldKey: `service:${svcKey}`,
        labelVi: `Hạng mục: ${entry.labelVi}`,
        labelEn: `Line Item: ${entry.labelEn}`,
        matchedText: message.slice(matched.start, matched.end),
        start: matched.start,
        end: matched.end,
        resolvedValue: svcKey,
      })
    }
  }

  const hoursRegex = /(\d+)\s*(giờ|gio|h|hours|hr|buổi| gói)/i
  const hoursMatch = hoursRegex.exec(message)
  if (hoursMatch && typeof hoursMatch.index === 'number') {
    const start = hoursMatch.index
    const end = start + hoursMatch[0].length
    citations.push({
      id: 'span_hours',
      fieldKey: 'estimated_hours',
      labelVi: 'Khối lượng trích xuất',
      labelEn: 'Extracted Effort',
      matchedText: message.slice(start, end),
      start,
      end,
      resolvedValue: `${estimatedHours}h`,
    })
  }

  const vatRegex = /(VAT\s*\d+%|GTGT\s*\d+%|hóa đơn\s*VAT|MISA|Sapo)/i
  const vatMatch = vatRegex.exec(message)
  if (vatMatch && typeof vatMatch.index === 'number') {
    const start = vatMatch.index
    const end = start + vatMatch[0].length
    citations.push({
      id: 'span_vat_accounting',
      fieldKey: 'accounting_vat',
      labelVi: 'Thuế & Nháp kế toán',
      labelEn: 'VAT & Accounting Draft',
      matchedText: message.slice(start, end),
      start,
      end,
      resolvedValue: `VAT ${vatRatePct}% · DRAFT_PENDING_TVAN`,
    })
  }

  return citations.sort((a, b) => a.start - b.start)
}

export function buildTvanDraftPreview(params: {
  format: TvanExportFormat
  provider: AccountingTargetProvider
  runId: string
  buyerName: string
  currency: SupportedCurrency
  lineItems: OpcLineItem[]
  financials: QuoteFinancialSummary
  language: SupportedLanguage
}): string {
  const { format, provider, runId, buyerName, currency, lineItems, financials, language } = params
  const pricedItems = lineItems.map((it) => {
    const svc = SERVICE_CATALOG[it.service]
    const label = svc ? (language === 'vi' ? svc.labelVi : svc.labelEn) : it.service
    return {
      code: it.service,
      name: label,
      qty: it.hours,
      unitPrice: it.isUnpriced ? null : Math.round(it.rate),
      lineSubtotal: it.isUnpriced ? null : Math.round(it.subtotal),
    }
  })

  if (format === 'CSV') {
    const header =
      'invoice_status,target_provider,requires_tvan_signature,legal_certified,run_id,buyer_name,item_code,item_name,qty,unit_price,line_subtotal,vat_rate_pct,vat_amount,grand_total,vietqr_memo'
    const rows = pricedItems.map(
      (it) =>
        `DRAFT_PENDING_TVAN,${provider},true,false,${runId},"${buyerName.replace(/"/g, '""')}",${it.code},"${it.name.replace(
          /"/g,
          '""'
        )}",${it.qty},${it.unitPrice ?? 'UNPRICED'},${it.lineSubtotal ?? 'UNPRICED'},${
          financials.vatRatePct
        },${Math.round(financials.vatAmount)},${Math.round(financials.grandTotal)},"${financials.vietQrMemo}"`
    )
    return [header, ...rows].join('\n')
  }

  if (format === 'XML') {
    const xmlItems = pricedItems
      .map(
        (it, idx) =>
          `    <HHDVu stt="${idx + 1}">\n      <MaHH>${escapeXml(it.code)}</MaHH>\n      <TenHH>${escapeXml(
            it.name
          )}</TenHH>\n      <SLuong>${it.qty}</SLuong>\n      <DGia>${
            it.unitPrice ?? 'UNPRICED'
          }</DGia>\n      <ThTien>${it.lineSubtotal ?? 'UNPRICED'}</ThTien>\n    </HHDVu>`
      )
      .join('\n')
    return [
      '<?xml version="1.0" encoding="UTF-8"?>',
      `<PreAccountingDraft status="DRAFT_PENDING_TVAN" provider="${provider}" requiresTvanSignature="true" legalCertified="false">`,
      `  <RunId>${escapeXml(runId)}</RunId>`,
      `  <BuyerName>${escapeXml(buyerName)}</BuyerName>`,
      `  <Currency>${currency}</Currency>`,
      `  <VietQrMemo>${escapeXml(financials.vietQrMemo)}</VietQrMemo>`,
      '  <DSHHDVu>',
      xmlItems,
      '  </DSHHDVu>',
      `  <TToan TgTCThue="${Math.round(financials.subtotal)}" TSuat="${financials.vatRatePct}%" TgTThue="${Math.round(
        financials.vatAmount
      )}" TgTTTBSo="${Math.round(financials.grandTotal)}" />`,
      '</PreAccountingDraft>',
    ].join('\n')
  }

  return JSON.stringify(
    {
      invoice_status: 'DRAFT_PENDING_TVAN',
      target_provider: provider,
      requires_tvan_signature: true,
      legal_certified: false,
      compliance_note: 'Decree 123/2020/ND-CP & Circular 78/2021/TT-BTC pre-accounting draft only',
      run_id: runId,
      buyer_name: buyerName,
      currency,
      vietqr_memo: financials.vietQrMemo,
      subtotal: Math.round(financials.subtotal),
      vat_rate_pct: financials.vatRatePct,
      vat_amount: Math.round(financials.vatAmount),
      total_amount: Math.round(financials.grandTotal),
      line_items: pricedItems,
    },
    null,
    2
  )
}

function escapeXml(raw: string): string {
  return raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function canonicalizePayload(payload: OpcActionPayload): string {
  const ordered = {
    attachments: [...payload.attachments],
    budget_amount: payload.budget_amount,
    budget_currency: payload.budget_currency,
    capability: payload.capability,
    connector: payload.connector,
    content: payload.content,
    expires_at: payload.expires_at,
    parameters: {
      amount: payload.parameters.amount,
      project_title: payload.parameters.project_title,
    },
    principal: payload.principal,
    recipient: payload.recipient,
  }
  return JSON.stringify(ordered)
}

export async function computeSha256Hex(input: string): Promise<string> {
  const subtle = globalThis.crypto?.subtle
  if (
    !subtle ||
    typeof subtle.digest !== 'function' ||
    typeof globalThis.TextEncoder === 'undefined'
  ) {
    throw new Error(
      'CRYPTO_UNAVAILABLE: Web Crypto SubtleCrypto SHA-256 is required for cryptographic approval.'
    )
  }
  const encoder = new globalThis.TextEncoder()
  const data = encoder.encode(input)
  const hashBuffer = await subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

export function formatDeterministicTimestamp(unixSeconds: number, timezone: string, language: SupportedLanguage): string {
  try {
    return new Intl.DateTimeFormat(language === 'vi' ? 'vi-VN' : 'en-US', {
      timeZone: timezone || 'Asia/Ho_Chi_Minh',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(new Date(unixSeconds * 1000))
  } catch {
    return new Date(unixSeconds * 1000).toISOString().slice(0, 16).replace('T', ' ')
  }
}

export type BffSyncMode = 'live_gateway' | 'unverified_idle' | 'failed_closed'

export interface GatewaySyncResult {
  synced: boolean
  endpoint: string
  mode: BffSyncMode
  serverRunId?: string
  serverActionDigest?: string
  serverRejected: boolean
  failedClosed: boolean
  httpStatus?: number
  errorCode?: string
  detail: string
}

export interface OpcClientSessionStatus {
  authenticated: boolean
  sub?: string
  workspaceId?: string
  allowedTenants?: string[]
  role?: 'owner' | 'operator' | 'viewer'
  exp?: number
  error?: string
  message?: string
}

export interface PilotARunInspection {
  ok: boolean
  httpStatus: number
  runId?: string
  status?: string
  checkpointStage?: string | null
  actionDigest?: string
  error?: string
}

export interface PilotADraftExportResult {
  ok: boolean
  httpStatus: number
  content?: string
  error?: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function extractBffErrorDetail(body: unknown, status: number): { errorCode?: string; detail: string } {
  if (isRecord(body)) {
    const rawDetail = isRecord(body.detail) ? body.detail : body
    const errCode =
      typeof rawDetail.error === 'string'
        ? rawDetail.error
        : typeof body.error === 'string'
        ? body.error
        : undefined
    const msg =
      typeof rawDetail.message === 'string'
        ? rawDetail.message
        : typeof body.message === 'string'
        ? body.message
        : undefined
    if (errCode && msg) {
      return { errorCode: errCode, detail: `HTTP ${status} (${errCode}): ${msg}` }
    }
    if (errCode) {
      return { errorCode: errCode, detail: `HTTP ${status} (${errCode})` }
    }
  }
  return { detail: `HTTP ${status}` }
}

export async function inspectPilotABffSession(): Promise<OpcClientSessionStatus> {
  try {
    const response = await fetch('/api/opc/pilot-a/session', {
      method: 'GET',
      credentials: 'same-origin',
      cache: 'no-store',
    })
    const body: unknown = await response.json()
    if (!response.ok || !isRecord(body) || body.authenticated !== true) {
      return {
        authenticated: false,
        error: isRecord(body) && typeof body.error === 'string' ? body.error : `http_${response.status}`,
        message: isRecord(body) && typeof body.message === 'string' ? body.message : undefined,
      }
    }
    return {
      authenticated: true,
      sub: typeof body.sub === 'string' ? body.sub : undefined,
      workspaceId: typeof body.workspaceId === 'string' ? body.workspaceId : undefined,
      allowedTenants: Array.isArray(body.allowedTenants)
        ? body.allowedTenants.filter((t): t is string => typeof t === 'string')
        : [],
      role:
        body.role === 'owner' || body.role === 'operator' || body.role === 'viewer'
          ? body.role
          : undefined,
      exp: typeof body.exp === 'number' ? body.exp : undefined,
    }
  } catch {
    return { authenticated: false, error: 'bff_session_unreachable' }
  }
}

export async function loginPilotABffSession(params: {
  credential: string
  workspaceId: string
  tenantId: string
  role?: 'owner' | 'operator' | 'viewer'
}): Promise<OpcClientSessionStatus> {
  try {
    const response = await fetch('/api/opc/pilot-a/session', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        credential: params.credential,
        workspace_id: params.workspaceId,
        tenant_id: params.tenantId,
        role: params.role || 'owner',
      }),
    })
    const body: unknown = await response.json()
    if (!response.ok || !isRecord(body) || body.authenticated !== true) {
      return {
        authenticated: false,
        error: isRecord(body) && typeof body.error === 'string' ? body.error : `http_${response.status}`,
        message: isRecord(body) && typeof body.message === 'string' ? body.message : undefined,
      }
    }
    return {
      authenticated: true,
      sub: typeof body.sub === 'string' ? body.sub : undefined,
      workspaceId: typeof body.workspaceId === 'string' ? body.workspaceId : undefined,
      allowedTenants: Array.isArray(body.allowedTenants)
        ? body.allowedTenants.filter((t): t is string => typeof t === 'string')
        : [],
      role:
        body.role === 'owner' || body.role === 'operator' || body.role === 'viewer'
          ? body.role
          : undefined,
      exp: typeof body.exp === 'number' ? body.exp : undefined,
    }
  } catch {
    return { authenticated: false, error: 'bff_login_network_error' }
  }
}

export async function logoutPilotABffSession(): Promise<void> {
  try {
    await fetch('/api/opc/pilot-a/session', {
      method: 'DELETE',
      credentials: 'same-origin',
    })
  } catch {
    // Fail-safe cookie clear attempt; local session state resets regardless.
  }
}

export async function syncPilotAZaloWebhook(payload: {
  tenantId: string
  eventId: string
  senderName: string
  senderContact: string
  messageText: string
  projectTitle: string
  requestedServices: string[]
  estimatedHours: number
  currency: SupportedCurrency
  language: SupportedLanguage
  extractionConfidence: number
}): Promise<GatewaySyncResult> {
  const endpoint = '/api/opc/pilot-a/webhook/zalo'
  const controller =
    typeof globalThis.AbortController !== 'undefined' ? new globalThis.AbortController() : null
  const timer = setTimeout(() => controller?.abort(), 5000)
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: payload.tenantId,
        event_id: payload.eventId,
        oa_id: 'oa_mekong_vn_01',
        sender_id: payload.senderContact.replace(/^zalo:/, ''),
        sender_name: payload.senderName,
        message_text: payload.messageText,
        requested_services: payload.requestedServices,
        estimated_hours: payload.estimatedHours,
        project_title: payload.projectTitle,
        currency: payload.currency,
        language: payload.language,
        extraction_confidence: payload.extractionConfidence,
      }),
      signal: controller?.signal,
    })
    clearTimeout(timer)
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    if (!response.ok) {
      const { errorCode, detail } = extractBffErrorDetail(body, response.status)
      return {
        synced: false,
        endpoint,
        mode: 'failed_closed',
        serverRejected: true,
        failedClosed: true,
        httpStatus: response.status,
        errorCode,
        detail,
      }
    }
    const serverRunId =
      isRecord(body) && typeof body.run_id === 'string' ? body.run_id : undefined
    const serverActionDigest =
      isRecord(body) && typeof body.action_digest === 'string' ? body.action_digest : undefined
    return {
      synced: true,
      endpoint,
      mode: 'live_gateway',
      serverRunId,
      serverActionDigest,
      serverRejected: false,
      failedClosed: false,
      httpStatus: response.status,
      detail: 'OK',
    }
  } catch {
    clearTimeout(timer)
    return {
      synced: false,
      endpoint,
      mode: 'failed_closed',
      serverRejected: true,
      failedClosed: true,
      errorCode: 'bff_network_unreachable',
      detail: 'BFF_UNREACHABLE',
    }
  }
}

export async function syncPilotADecision(payload: {
  tenantId: string
  runId: string
  decision: 'approve' | 'reject' | 'handoff'
  actionDigest: string
  revisionNotes: string
}): Promise<GatewaySyncResult> {
  const endpoint = '/api/opc/pilot-a/decide'
  const controller =
    typeof globalThis.AbortController !== 'undefined' ? new globalThis.AbortController() : null
  const timer = setTimeout(() => controller?.abort(), 5000)
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: payload.tenantId,
        run_id: payload.runId,
        decision: payload.decision,
        action_digest: payload.actionDigest,
        revision_notes: payload.revisionNotes,
      }),
      signal: controller?.signal,
    })
    clearTimeout(timer)
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      body = null
    }
    if (!response.ok) {
      const { errorCode, detail } = extractBffErrorDetail(body, response.status)
      return {
        synced: false,
        endpoint,
        mode: 'failed_closed',
        serverRejected: true,
        failedClosed: true,
        httpStatus: response.status,
        errorCode,
        detail,
      }
    }
    return {
      synced: true,
      endpoint,
      mode: 'live_gateway',
      serverRunId: payload.runId,
      serverRejected: false,
      failedClosed: false,
      httpStatus: response.status,
      detail: 'OK',
    }
  } catch {
    clearTimeout(timer)
    return {
      synced: false,
      endpoint,
      mode: 'failed_closed',
      serverRejected: true,
      failedClosed: true,
      errorCode: 'bff_network_unreachable',
      detail: 'BFF_UNREACHABLE',
    }
  }
}

export async function fetchPilotARunSummary(
  runId: string,
  tenantId: string
): Promise<PilotARunInspection> {
  try {
    const query = new URLSearchParams({ tenant_id: tenantId })
    const response = await fetch(
      `/api/opc/pilot-a/runs/${encodeURIComponent(runId)}?${query.toString()}`,
      {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
      }
    )
    const body: unknown = await response.json()
    if (!response.ok || !isRecord(body)) {
      const { errorCode, detail } = extractBffErrorDetail(body, response.status)
      return {
        ok: false,
        httpStatus: response.status,
        error: errorCode || detail,
      }
    }
    return {
      ok: true,
      httpStatus: response.status,
      runId: typeof body.run_id === 'string' ? body.run_id : runId,
      status: typeof body.status === 'string' ? body.status : undefined,
      checkpointStage:
        typeof body.checkpoint_stage === 'string' ? body.checkpoint_stage : null,
      actionDigest: typeof body.action_digest === 'string' ? body.action_digest : undefined,
    }
  } catch {
    return { ok: false, httpStatus: 502, error: 'bff_network_unreachable' }
  }
}

export async function fetchPilotADraftExport(params: {
  runId: string
  tenantId: string
  format: TvanExportFormat
  vatRatePct: VatRatePct
  provider: AccountingTargetProvider
}): Promise<PilotADraftExportResult> {
  try {
    const query = new URLSearchParams({
      tenant_id: params.tenantId,
      fmt: params.format.toLowerCase(),
      vat_rate_pct: String(params.vatRatePct),
      target_provider: params.provider,
    })
    const response = await fetch(
      `/api/opc/pilot-a/draft-export/${encodeURIComponent(params.runId)}?${query.toString()}`,
      {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
      }
    )
    if (!response.ok) {
      let body: unknown = null
      try {
        body = await response.json()
      } catch {
        body = null
      }
      const { errorCode, detail } = extractBffErrorDetail(body, response.status)
      return {
        ok: false,
        httpStatus: response.status,
        error: errorCode || detail,
      }
    }
    const content = await response.text()
    return {
      ok: true,
      httpStatus: response.status,
      content,
    }
  } catch {
    return { ok: false, httpStatus: 502, error: 'bff_network_unreachable' }
  }
}
