import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { ChartDataPoint } from '../types';
import { formatCurrency } from '../utils/calculator';

interface ChartSectionProps {
  data: ChartDataPoint[];
}

export const ChartSection: React.FC<ChartSectionProps> = ({ data }) => {
  return (
    <div className="card">
      <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
        Cost Comparison Over Time
      </h2>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="currentCostGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="mekongCostGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="month"
              label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
              tickFormatter={(month) => month % 6 === 0 ? `M${month}` : ''}
            />
            <YAxis
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              labelFormatter={(label) => `Month ${label}`}
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '12px'
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="currentCost"
              name="Current Costs"
              stroke="#ef4444"
              strokeWidth={2}
              fill="url(#currentCostGradient)"
            />
            <Area
              type="monotone"
              dataKey="mekongCost"
              name="Mekong CLI Costs"
              stroke="#0ea5e9"
              strokeWidth={2}
              fill="url(#mekongCostGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Savings Chart */}
      <div className="mt-6">
        <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
          Cumulative Savings
        </h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="month"
                tickFormatter={(month) => month % 12 === 0 ? `Y${month/12}` : ''}
              />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                labelFormatter={(label) => `Month ${label}`}
              />
              <Line
                type="monotone"
                dataKey="cumulativeSavings"
                name="Cumulative Savings"
                stroke="#22c55e"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
