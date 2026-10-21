'use client'

import { useState, useEffect, useCallback } from 'react'
import { CheckCircle2, CreditCard, AlertTriangle, Loader2, Lock } from 'lucide-react'
import { resolveEngineApiUrl } from '@/lib/demo-guard'

export interface Transaction {
  id: string
  success: boolean
  message: string
}

export interface BraintreeCheckoutProps {
  amount: string
  description?: string
  onSuccess?: (transaction: Transaction) => void
  onError?: (error: string) => void
  className?: string
}

interface BraintreeWindow {
  braintree: {
    dropin: {
      create: (options: {
        authorization: string
        container: string
      }) => Promise<{ requestPaymentMethod: () => Promise<{ nonce: string }> }>
    }
  }
}

const API_URL = resolveEngineApiUrl()

export function BraintreeCheckout({
  amount,
  description = 'Payment',
  onSuccess,
  onError,
  className = '',
}: BraintreeCheckoutProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [success, setSuccess] = useState(false)
  const [braintreeReady, setBraintreeReady] = useState(false)

  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://js.braintreegateway.com/web/dropin/1.43.0/js/dropin.min.js'
    script.async = true
    script.onload = () => setBraintreeReady(true)
    script.onerror = () => setError('Không thể tải Braintree SDK')
    document.body.appendChild(script)
    return () => {
      document.body.removeChild(script)
    }
  }, [])

  useEffect(() => {
    if (!braintreeReady) return
    const initDropin = async () => {
      try {
        const tokenRes = await fetch(`${API_URL}/payments/client-token`)
        if (!tokenRes.ok) {
          const errData = await tokenRes.json()
          throw new Error(errData.detail || 'Không lấy được token')
        }
        const { token } = await tokenRes.json()
        const braintree = (window as unknown as BraintreeWindow).braintree
        await braintree.dropin.create({ authorization: token, container: '#dropin-container' })
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Lỗi khởi tạo thanh toán')
        setLoading(false)
      }
    }
    initDropin()
  }, [braintreeReady])

  const handleSubmit = useCallback(async () => {
    setProcessing(true)
    setError(null)
    try {
      const container = document.querySelector('#dropin-container')
      if (!container) throw new Error('Không tìm thấy form thanh toán')

      const res = await fetch(`${API_URL}/payments/mock-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nonce: 'mock-nonce', amount, description }),
      })
      const data = await res.json()
      if (data.success) {
        setSuccess(true)
        onSuccess?.(data)
      } else {
        throw new Error(data.message || 'Thanh toán thất bại')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Lỗi xử lý thanh toán'
      setError(message)
      onError?.(message)
    } finally {
      setProcessing(false)
    }
  }, [amount, description, onSuccess, onError])

  if (success) {
    return (
      <div className={`rounded-xl border border-green-500/20 bg-green-500/10 p-6 text-center ${className}`}>
        <CheckCircle2 className="w-10 h-10 text-green-400 mx-auto mb-4" aria-hidden="true" />
        <h3 className="text-xl font-bold text-green-400 mb-2">Thanh Toán Thành Công!</h3>
        <p className="text-green-300/80 tabular-nums">Cảm ơn bạn đã thanh toán ${amount}</p>
      </div>
    )
  }

  return (
    <div className={`rounded-xl border border-white/10 bg-white/5 p-6 ${className}`}>
      <div className="mb-6">
        <h3 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-blue-400" aria-hidden="true" /> Thanh Toán
        </h3>
        <p className="text-white/60 text-sm tabular-nums">{description} - ${amount}</p>
      </div>

      {error && (
        <div role="alert" className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" aria-hidden="true" /> {error}
        </div>
      )}

      <div id="dropin-container" className="mb-6 min-h-[200px]">
        {loading && (
          <div className="flex items-center justify-center h-[200px] text-white/60">
            <Loader2 className="w-5 h-5 animate-spin mr-2" aria-hidden="true" />
            Đang tải form thanh toán...
          </div>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading || processing}
        className={`w-full min-h-[44px] py-3 px-6 rounded-lg font-semibold text-white transition-all duration-200 flex items-center justify-center gap-2 ${
          loading || processing
            ? 'bg-white/10 cursor-not-allowed'
            : 'bg-linear-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 shadow-lg hover:shadow-xl cursor-pointer'
        }`}
      >
        {processing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            Đang xử lý...
          </>
        ) : (
          <span className="tabular-nums">Thanh Toán ${amount}</span>
        )}
      </button>

      <p className="text-center text-white/50 text-xs mt-4 flex items-center justify-center gap-1.5">
        <Lock className="w-3.5 h-3.5" aria-hidden="true" /> Thanh toán được bảo mật bởi Braintree/PayPal
      </p>
    </div>
  )
}

export default BraintreeCheckout
