import { useState, useRef } from 'react';
import { InputSection } from './components/input-section';
import { ResultsSection } from './components/results-section';
import { ChartSection } from './components/chart-section';
import { ExportButton } from './components/export-button';
import { calculateROI, generateChartData } from './utils/calculator';
import { CalculatorInputs } from './types';

const defaultInputs: CalculatorInputs = {
  currentEngineerCount: 10,
  currentAvgSalary: 150000,
  currentToolCosts: 2000,
  currentOpexMonthly: 5000,
  mekongSubscription: 149,
  mekongMcuUsage: 500,
  mekongMcuPrice: 0.29,
  projectionYears: 3
};

function App() {
  const [inputs, setInputs] = useState<CalculatorInputs>(defaultInputs);
  const [darkMode, setDarkMode] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const results = calculateROI(inputs);
  const chartData = generateChartData(inputs);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 transition-colors">
        {/* Header */}
        <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src="/logo.svg" alt="Mekong CLI" className="w-10 h-10" />
              <div>
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  Mekong CLI
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  ROI Calculator
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                aria-label="Toggle dark mode"
              >
                {darkMode ? (
                  <svg className="w-6 h-6 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                  </svg>
                )}
              </button>
              <ExportButton contentRef={contentRef as React.RefObject<HTMLDivElement>} />
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div ref={contentRef} className="space-y-6">
            {/* Input Section */}
            <InputSection inputs={inputs} onChange={setInputs} />

            {/* Results Section */}
            <ResultsSection results={results} />

            {/* Charts Section */}
            <ChartSection data={chartData} />
          </div>

          {/* Footer */}
          <footer className="mt-12 text-center text-slate-500 dark:text-slate-400 text-sm">
            <p>Mekong CLI - AI-operated business platform</p>
            <p className="mt-1">
              <a
                href="https://agencyos.network"
                target="_blank"
                rel="noopener noreferrer"
                className="text-mekong-600 hover:text-mekong-700 dark:text-mekong-400"
              >
                agencyos.network
              </a>
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default App;
