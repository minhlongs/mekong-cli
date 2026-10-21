import React, { useState, useEffect } from 'react';
import { simulateVietQR } from '../services/api';
import { VietQRSimulateResponse } from '../types/api';

interface VietQRModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSimulationComplete?: (resp: VietQRSimulateResponse) => void;
}

export const VietQRModal: React.FC<VietQRModalProps> = ({
  isOpen,
  onClose,
  onSimulationComplete
}) => {
  const [amount, setAmount] = useState<number>(250000);
  const [bankCode, setBankCode] = useState<string>('VCB');
  const [simData, setSimData] = useState<VietQRSimulateResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [paymentConfirmed, setPaymentConfirmed] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setPaymentConfirmed(false);
      handleGenerate();
    }
  }, [isOpen, amount, bankCode]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const resp = await simulateVietQR(amount, undefined, bankCode);
      setSimData(resp);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = () => {
    setPaymentConfirmed(true);
    if (simData && onSimulationComplete) {
      onSimulationComplete(simData);
    }
  };

  const handleCopyOrder = () => {
    if (simData?.order_id) {
      navigator.clipboard?.writeText(simData.order_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-md bg-[#11131A] border border-[#2D3748] rounded-xl shadow-2xl overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1E2230] bg-[#161923]">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
              QR
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">VietQR payment-flow demo</h3>
              <p className="text-[11px] text-amber-200">No payment, webhook verification, or credit occurs here.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-[#181B26]"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          {/* Amount Presets */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Example amount (demo data only)</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { vnd: 100000, mcu: '100 demo units' },
                { vnd: 250000, mcu: '250 demo units' },
                { vnd: 1000000, mcu: '1,000 demo units' }
              ].map(tier => (
                <button
                  key={tier.vnd}
                  onClick={() => setAmount(tier.vnd)}
                  className={`py-2 px-2 text-center rounded-lg border text-xs font-mono transition-all ${
                    amount === tier.vnd
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                      : 'bg-[#090A0F] border-[#1E2230] text-gray-400 hover:border-[#2D3748]'
                  }`}
                >
                  <div className="font-bold">{tier.vnd.toLocaleString()} đ</div>
                  <div className="text-[10px] text-emerald-400/80">{tier.mcu}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Bank Selector */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Example bank label</label>
            <div className="flex gap-2">
              {['VCB', 'MB', 'TCB'].map(b => (
                <button
                  key={b}
                  onClick={() => setBankCode(b)}
                  className={`flex-1 py-1.5 rounded-lg border text-xs font-bold font-mono transition-all ${
                    bankCode === b
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                      : 'bg-[#090A0F] border-[#1E2230] text-gray-400 hover:border-[#2D3748]'
                  }`}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>

          {/* No payable QR is generated in this demo. */}
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white text-slate-900 shadow-inner">
            {loading ? (
              <div className="h-48 flex items-center justify-center font-mono text-xs text-gray-500">
                Generating VietQR payload...
              </div>
            ) : (
              <div className="flex flex-col items-center text-center">
                <div className="w-44 h-44 bg-amber-50 border-2 border-amber-300 rounded-lg p-4 flex flex-col items-center justify-center relative shadow-sm text-amber-950">
                  <span className="text-2xl font-black tracking-widest">DEMO</span>
                  <span className="mt-2 text-xs">No payable QR code</span>
                  {paymentConfirmed && (
                    <div className="absolute inset-0 bg-amber-700/95 rounded-lg flex flex-col items-center justify-center text-white p-3">
                      <span className="text-3xl mb-1">✓</span>
                      <span className="font-bold text-xs uppercase tracking-wide">Simulation complete</span>
                      <span className="text-[10px] mt-1">No credits were issued</span>
                    </div>
                  )}
                </div>

                <div className="mt-3 text-xs font-mono font-bold text-slate-800">
                  {amount.toLocaleString('vi-VN')} VND ({simData?.simulated_mcu || 250} demo units)
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                  Order: <span className="font-bold">{simData?.order_id || 'ORD-9842'}</span>
                </div>
              </div>
            )}
          </div>

          {/* Explicit demo status; no cryptographic verification is claimed. */}
          <div className="p-2.5 rounded-lg bg-[#090A0F] border border-[#1E2230] text-[10px] font-mono space-y-1">
            <div className="flex justify-between text-gray-400">
              <span>Webhook verification:</span>
              <span className="text-amber-300 truncate max-w-[200px]">
                Not performed
              </span>
            </div>
            <div className="flex justify-between text-gray-500">
              <span>Environment:</span>
              <span>Demo only</span>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3 border-t border-[#1E2230] bg-[#161923] flex items-center gap-2">
          <button
            onClick={handleCopyOrder}
            className="flex-1 py-2 rounded-lg bg-[#090A0F] border border-[#2D3748] text-gray-300 hover:text-white text-xs font-medium transition-colors"
          >
            {copied ? '✓ Order Copied' : 'Copy Reference'}
          </button>
          <button
            onClick={handleRunSimulation}
            disabled={paymentConfirmed}
            className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
              paymentConfirmed
                ? 'bg-emerald-600 text-white cursor-default'
                : 'bg-emerald-500 hover:bg-emerald-400 text-black shadow-[0_0_15px_rgba(16,185,129,0.3)]'
            }`}
          >
            {paymentConfirmed ? '✓ Demo complete' : 'Run demo simulation'}
          </button>
        </div>
      </div>
    </div>
  );
};
