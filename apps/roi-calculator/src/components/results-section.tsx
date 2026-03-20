import React from 'react';
import { ROIResults } from '../types';
import { formatCurrency, formatPercent, formatDuration } from '../utils/calculator';

interface ResultsSectionProps {
  results: ROIResults;
}

export const ResultsSection: React.FC<ResultsSectionProps> = ({ results }) => {
  const isPositiveROI = results.totalSavings > 0;

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
        ROI Analysis Results
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Total Savings */}
        <div className="stat-card">
          <div className="stat-value">{formatCurrency(results.totalSavings)}</div>
          <div className="stat-label">Total Savings</div>
          <div className="text-sm mt-2 opacity-90">
            {formatPercent(results.savingsPercent)} reduction
          </div>
        </div>

        {/* Payback Period */}
        <div className="stat-card bg-gradient-to-br from-green-500 to-green-700">
          <div className="stat-value">{formatDuration(results.paybackMonths)}</div>
          <div className="stat-label">Payback Period</div>
          <div className="text-sm mt-2 opacity-90">
            Time to break even
          </div>
        </div>

        {/* 3-Year ROI */}
        <div className="stat-card bg-gradient-to-br from-purple-500 to-purple-700">
          <div className="stat-value">{formatPercent(results.threeYearRoi)}</div>
          <div className="stat-label">3-Year ROI</div>
          <div className="text-sm mt-2 opacity-90">
            Return on investment
          </div>
        </div>

        {/* NPV */}
        <div className="stat-card bg-gradient-to-br from-orange-500 to-orange-700">
          <div className="stat-value">{formatCurrency(results.npv)}</div>
          <div className="stat-label">Net Present Value</div>
          <div className="text-sm mt-2 opacity-90">
            10% discount rate
          </div>
        </div>

        {/* Monthly Comparison */}
        <div className="stat-card bg-gradient-to-br from-blue-500 to-blue-700">
          <div className="stat-value">{formatCurrency(results.monthlySavings)}</div>
          <div className="stat-label">Monthly Savings</div>
          <div className="text-sm mt-2 opacity-90">
            {formatCurrency(results.currentMonthlyCost)} → {formatCurrency(results.mekongMonthlyCost)}
          </div>
        </div>

        {/* Cost Comparison */}
        <div className="stat-card bg-gradient-to-br from-teal-500 to-teal-700">
          <div className="stat-value">{formatCurrency(results.mekongTotalCost)}</div>
          <div className="stat-label">Total Mekong Cost</div>
          <div className="text-sm mt-2 opacity-90">
            vs {formatCurrency(results.currentTotalCost)} current
          </div>
        </div>
      </div>

      {/* ROI Status Banner */}
      <div className={`mt-6 p-4 rounded-lg ${
        isPositiveROI
          ? 'bg-green-100 dark:bg-green-900 border border-green-300 dark:border-green-700'
          : 'bg-amber-100 dark:bg-amber-900 border border-amber-300 dark:border-amber-700'
      }`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">{isPositiveROI ? '✅' : '⚠️'}</span>
          <div>
            <p className={`font-semibold ${isPositiveROI ? 'text-green-800 dark:text-green-200' : 'text-amber-800 dark:text-amber-200'}`}>
              {isPositiveROI
                ? 'Positive ROI - Mekong CLI saves you money!'
                : 'Review your inputs - costs may be higher than expected'}
            </p>
            <p className={`text-sm ${isPositiveROI ? 'text-green-700 dark:text-green-300' : 'text-amber-700 dark:text-amber-300'}`}>
              {isPositiveROI
                ? `You'll save ${formatCurrency(results.totalSavings)} over ${results.paybackMonths < 12 ? 'the first year' : 'the projection period'}`
                : 'Consider adjusting engineer count or subscription tier'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
