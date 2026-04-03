/**
 * VnstockTool — Native Vietnamese stock data tool for Mekong CLI.
 *
 * Fetches data directly from TCBS API (no Python dependency, no MCP).
 * Baked into the single executable for Enterprise B2B delivery.
 *
 * TCBS API endpoints (public, no auth required):
 * - Financial report: https://apipubaws.tcbs.com.vn/tcanalysis/v1/finance/{ticker}/financialratio
 * - Price history:    https://apipubaws.tcbs.com.vn/stock-insight/v2/stock/bars-long-term
 * - Company overview: https://apipubaws.tcbs.com.vn/tcanalysis/v1/ticker/{ticker}/overview
 */

import { z } from 'zod/v4'
import { buildTool } from '../../Tool.js'
import { lazySchema } from '../../utils/lazySchema.js'

const TCBS_BASE = 'https://apipubaws.tcbs.com.vn'

const inputSchema = lazySchema(() =>
  z.strictObject({
    action: z
      .enum(['financial_report', 'credit_score', 'price_history', 'overview'])
      .describe('Type of data to fetch'),
    ticker: z
      .string()
      .describe('Vietnamese stock ticker symbol (e.g., VNM, FPT, VCB)'),
    start_date: z
      .string()
      .optional()
      .describe('Start date for price history (YYYY-MM-DD)'),
    end_date: z
      .string()
      .optional()
      .describe('End date for price history (YYYY-MM-DD)'),
  }),
)
type InputSchema = ReturnType<typeof inputSchema>

const outputSchema = lazySchema(() =>
  z.object({
    ticker: z.string(),
    action: z.string(),
    data: z.any(),
    error: z.string().optional(),
  }),
)

const VNSTOCK_TOOL_NAME = 'Vnstock'

const DESCRIPTION = `Fetch Vietnamese stock market data (financial reports, credit scoring ratios, price history, company overview). Uses TCBS public API. Tickers are Vietnamese stock codes like VNM, FPT, VCB, HPG, MWG.`

async function tcbsFetch(path: string): Promise<any> {
  const url = `${TCBS_BASE}${path}`
  const resp = await fetch(url, {
    headers: {
      'User-Agent': 'Mekong-CLI/1.0',
      Accept: 'application/json',
    },
  })
  if (!resp.ok) {
    throw new Error(`TCBS API ${resp.status}: ${resp.statusText}`)
  }
  return resp.json()
}

async function getFinancialReport(ticker: string): Promise<any> {
  const data = await tcbsFetch(
    `/tcanalysis/v1/finance/${ticker.toUpperCase()}/financialratio?yearly=0&isAll=true`,
  )
  // Extract latest 4 quarters
  const rows = Array.isArray(data) ? data.slice(0, 4) : []
  return {
    ticker: ticker.toUpperCase(),
    periods: rows.length,
    data: rows,
  }
}

async function getCreditScore(ticker: string): Promise<any> {
  const data = await tcbsFetch(
    `/tcanalysis/v1/finance/${ticker.toUpperCase()}/financialratio?yearly=0&isAll=false`,
  )
  const latest = Array.isArray(data) && data.length > 0 ? data[0] : {}

  // Extract credit-relevant ratios
  const creditKeys = [
    'roe', 'roa', 'debtOnEquity', 'debtOnAsset',
    'currentPayment', 'quickPayment', 'grossProfitMargin',
    'operatingProfitMargin', 'netProfitMargin', 'revenue',
    'postTaxProfit', 'assetOnEquity',
  ]

  const creditRatios: Record<string, any> = {}
  for (const key of creditKeys) {
    if (latest[key] !== undefined) {
      creditRatios[key] = latest[key]
    }
  }

  return {
    ticker: ticker.toUpperCase(),
    credit_ratios: creditRatios,
    full_latest: latest,
  }
}

async function getPriceHistory(
  ticker: string,
  startDate?: string,
  endDate?: string,
): Promise<any> {
  const end = endDate || new Date().toISOString().split('T')[0]
  const start = startDate || (() => {
    const d = new Date()
    d.setMonth(d.getMonth() - 3)
    return d.toISOString().split('T')[0]
  })()

  // Convert dates to timestamps
  const startTs = Math.floor(new Date(start).getTime() / 1000)
  const endTs = Math.floor(new Date(end).getTime() / 1000)

  const data = await tcbsFetch(
    `/stock-insight/v2/stock/bars-long-term?ticker=${ticker.toUpperCase()}&type=stock&resolution=D&from=${startTs}&to=${endTs}`,
  )

  const bars = data?.data || []
  return {
    ticker: ticker.toUpperCase(),
    start_date: start,
    end_date: end,
    count: bars.length,
    ohlcv: bars.slice(-30).map((b: any) => ({
      date: new Date(b.tradingDate).toISOString().split('T')[0],
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
      volume: b.volume,
    })),
  }
}

async function getOverview(ticker: string): Promise<any> {
  const data = await tcbsFetch(
    `/tcanalysis/v1/ticker/${ticker.toUpperCase()}/overview`,
  )
  return {
    ticker: ticker.toUpperCase(),
    name: data?.companyName,
    exchange: data?.exchange,
    industry: data?.industry,
    market_cap: data?.marketCap,
    outstanding_shares: data?.outstandingShare,
    pe: data?.pe,
    pb: data?.pb,
    dividend_yield: data?.dividendYield,
    beta: data?.beta,
    summary: data?.companyProfile?.slice(0, 500),
  }
}

export const VnstockTool = buildTool<InputSchema>(
  {
    name: VNSTOCK_TOOL_NAME,
    description: DESCRIPTION,
    inputSchema,
    isAlwaysAvailable: true,
    isReadOnly: true,
    async call({ input }) {
      const { action, ticker, start_date, end_date } = input

      // Validate ticker format
      if (!/^[A-Z0-9]{1,10}$/i.test(ticker)) {
        return {
          type: 'tool_result' as const,
          tool_use_id: '',
          content: JSON.stringify({
            ticker,
            action,
            error: `Invalid ticker format: ${ticker}`,
          }),
        }
      }

      try {
        let data: any
        switch (action) {
          case 'financial_report':
            data = await getFinancialReport(ticker)
            break
          case 'credit_score':
            data = await getCreditScore(ticker)
            break
          case 'price_history':
            data = await getPriceHistory(ticker, start_date, end_date)
            break
          case 'overview':
            data = await getOverview(ticker)
            break
        }

        return {
          type: 'tool_result' as const,
          tool_use_id: '',
          content: JSON.stringify({ ticker: ticker.toUpperCase(), action, data }),
        }
      } catch (err: any) {
        return {
          type: 'tool_result' as const,
          tool_use_id: '',
          content: JSON.stringify({
            ticker: ticker.toUpperCase(),
            action,
            error: err.message,
          }),
        }
      }
    },
    userFacingName() {
      return VNSTOCK_TOOL_NAME
    },
    renderToolUseMessage(input) {
      return `Fetching ${input.action} for ${input.ticker}...`
    },
    renderToolResultMessage(result) {
      try {
        const parsed = JSON.parse(
          typeof result === 'string' ? result : (result as any).content || '{}',
        )
        if (parsed.error) return `Error: ${parsed.error}`
        return `${parsed.ticker} ${parsed.action}: data retrieved`
      } catch {
        return 'Vnstock data retrieved'
      }
    },
  },
  { outputSchema },
)
