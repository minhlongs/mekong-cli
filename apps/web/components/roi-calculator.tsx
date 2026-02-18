"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function ROICalculator() {
  const [revenue, setRevenue] = useState(50000)

  const monthlyRaaS = revenue * 0.3
  const yearlyRaaS = monthlyRaaS * 12
  const roi = ((yearlyRaaS - (revenue * 12 * 0.1)) / (revenue * 12 * 0.1)) * 100

  return (
    <Card className="bg-gradient-to-br from-cyan-500/10 via-purple-500/10 to-pink-500/10 border-cyan-500/30 backdrop-blur-sm">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
            ROI Calculator
          </CardTitle>
          <Badge className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0">
            Interactive
          </Badge>
        </div>
        <CardDescription className="text-gray-300">
          Tính toán doanh thu tiềm năng từ RaaS model
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Doanh thu hiện tại/tháng (USD)
          </label>
          <input
            type="range"
            min="10000"
            max="500000"
            step="10000"
            value={revenue}
            onChange={(e) => setRevenue(Number(e.target.value))}
            className="w-full h-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between mt-2">
            <span className="text-xs text-gray-400">$10K</span>
            <span className="text-xl font-bold text-cyan-400">${(revenue/1000).toFixed(0)}K</span>
            <span className="text-xs text-gray-400">$500K</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-gradient-to-br from-cyan-500/20 to-transparent border border-cyan-500/30">
            <div className="text-xs text-gray-400 mb-1">RaaS/Tháng</div>
            <div className="text-2xl font-bold text-cyan-400">${(monthlyRaaS/1000).toFixed(1)}K</div>
          </div>
          <div className="p-4 rounded-lg bg-gradient-to-br from-purple-500/20 to-transparent border border-purple-500/30">
            <div className="text-xs text-gray-400 mb-1">RaaS/Năm</div>
            <div className="text-2xl font-bold text-purple-400">${(yearlyRaaS/1000).toFixed(0)}K</div>
          </div>
          <div className="p-4 rounded-lg bg-gradient-to-br from-pink-500/20 to-transparent border border-pink-500/30">
            <div className="text-xs text-gray-400 mb-1">ROI</div>
            <div className="text-2xl font-bold text-pink-400">{roi.toFixed(0)}%</div>
          </div>
        </div>

        <div className="text-xs text-gray-400 pt-2 border-t border-gray-700">
          * Giả định: 30% doanh thu từ RaaS model, chi phí vận hành 10%
        </div>
      </CardContent>
    </Card>
  )
}
