import React from 'react';
import { CalculatorInputs } from '../types';

interface InputSectionProps {
  inputs: CalculatorInputs;
  onChange: (inputs: CalculatorInputs) => void;
}

export const InputSection: React.FC<InputSectionProps> = ({ inputs, onChange }) => {
  const handleChange = (field: keyof CalculatorInputs, value: number) => {
    onChange({ ...inputs, [field]: value });
  };

  const scenarios = [
    {
      name: 'Startup',
      description: 'Small team, basic automation',
      data: {
        currentEngineerCount: 3,
        currentAvgSalary: 120000,
        currentToolCosts: 500,
        currentOpexMonthly: 2000,
        mekongSubscription: 49,
        mekongMcuUsage: 200,
        projectionYears: 3
      }
    },
    {
      name: 'Growth',
      description: 'Medium team, expanding ops',
      data: {
        currentEngineerCount: 10,
        currentAvgSalary: 150000,
        currentToolCosts: 2000,
        currentOpexMonthly: 5000,
        mekongSubscription: 149,
        mekongMcuUsage: 500,
        projectionYears: 3
      }
    },
    {
      name: 'Enterprise',
      description: 'Large team, full automation',
      data: {
        currentEngineerCount: 50,
        currentAvgSalary: 180000,
        currentToolCosts: 10000,
        currentOpexMonthly: 20000,
        mekongSubscription: 499,
        mekongMcuUsage: 2000,
        projectionYears: 3
      }
    }
  ];

  const applyScenario = (scenarioData: Partial<CalculatorInputs>) => {
    onChange({ ...inputs, ...scenarioData });
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
        Input Parameters
      </h2>

      {/* Quick Scenarios */}
      <div className="mb-6">
        <label className="input-label mb-2 block">Quick Scenarios</label>
        <div className="flex gap-2 flex-wrap">
          {scenarios.map((scenario) => (
            <button
              key={scenario.name}
              onClick={() => applyScenario(scenario.data)}
              className="px-4 py-2 bg-mekong-100 dark:bg-mekong-900 text-mekong-700 dark:text-mekong-300
                         rounded-lg hover:bg-mekong-200 dark:hover:bg-mekong-800 transition-colors text-sm"
            >
              {scenario.name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Current Costs */}
        <div className="space-y-4">
          <h3 className="font-semibold text-slate-800 dark:text-slate-200 border-b pb-2">
            Current Monthly Costs
          </h3>

          <div className="input-group">
            <label className="input-label">Number of Engineers</label>
            <input
              type="number"
              value={inputs.currentEngineerCount}
              onChange={(e) => handleChange('currentEngineerCount', Number(e.target.value))}
              className="input-field"
              min="0"
            />
          </div>

          <div className="input-group">
            <label className="input-label">Average Annual Salary ($)</label>
            <input
              type="number"
              value={inputs.currentAvgSalary}
              onChange={(e) => handleChange('currentAvgSalary', Number(e.target.value))}
              className="input-field"
              min="0"
              step="1000"
            />
          </div>

          <div className="input-group">
            <label className="input-label">Tool Costs Monthly ($)</label>
            <input
              type="number"
              value={inputs.currentToolCosts}
              onChange={(e) => handleChange('currentToolCosts', Number(e.target.value))}
              className="input-field"
              min="0"
            />
          </div>

          <div className="input-group">
            <label className="input-label">Other OpEx Monthly ($)</label>
            <input
              type="number"
              value={inputs.currentOpexMonthly}
              onChange={(e) => handleChange('currentOpexMonthly', Number(e.target.value))}
              className="input-field"
              min="0"
            />
          </div>
        </div>

        {/* Mekong Costs */}
        <div className="space-y-4">
          <h3 className="font-semibold text-slate-800 dark:text-slate-200 border-b pb-2">
            Mekong CLI Costs
          </h3>

          <div className="input-group">
            <label className="input-label">Subscription Tier ($/month)</label>
            <select
              value={inputs.mekongSubscription}
              onChange={(e) => handleChange('mekongSubscription', Number(e.target.value))}
              className="input-field"
            >
              <option value={49}>Starter - $49/mo</option>
              <option value={149}>Growth - $149/mo</option>
              <option value={499}>Enterprise - $499/mo</option>
            </select>
          </div>

          <div className="input-group">
            <label className="input-label">Monthly MCU Usage</label>
            <input
              type="number"
              value={inputs.mekongMcuUsage}
              onChange={(e) => handleChange('mekongMcuUsage', Number(e.target.value))}
              className="input-field"
              min="0"
            />
            <p className="text-xs text-slate-500">Typical: 200-2000 MCU/month</p>
          </div>

          <div className="input-group">
            <label className="input-label">MCU Price ($)</label>
            <input
              type="number"
              value={inputs.mekongMcuPrice}
              onChange={(e) => handleChange('mekongMcuPrice', Number(e.target.value))}
              className="input-field"
              min="0"
              step="0.01"
            />
            <p className="text-xs text-slate-500">Default: $0.29/MCU</p>
          </div>

          <div className="input-group">
            <label className="input-label">Projection Period (years)</label>
            <select
              value={inputs.projectionYears}
              onChange={(e) => handleChange('projectionYears', Number(e.target.value))}
              className="input-field"
            >
              <option value={1}>1 Year</option>
              <option value={3}>3 Years</option>
              <option value={5}>5 Years</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};
